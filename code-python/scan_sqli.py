import requests
import urllib.parse
import copy
import difflib
from colorama import Fore, Style

class SQLHeuristicEngine:
    def __init__(self, target_url):
        self.target = target_url
        self.parsed = urllib.parse.urlparse(target_url)
        self.params = urllib.parse.parse_qs(self.parsed.query)
        self.base_url = target_url.split("?")[0]
        
        # Header standar
        self.headers = {'User-Agent': 'ZeroBurst-HeuristicScanner/8.0'}
        
        # 1.1 PARAMETER MAPPING & CONTEXT
        # Kita simpan respon awal sebagai "Baseline" (Kondisi Normal)
        print(f"{Fore.CYAN}[*] Establishing Baseline Request...{Style.RESET_ALL}")
        try:
            self.baseline_resp = requests.get(target_url, headers=self.headers, timeout=10)
            self.baseline_len = len(self.baseline_resp.text)
            self.baseline_code = self.baseline_resp.status_code
            print(f"   └── Baseline established: {self.baseline_code} OK | Size: {self.baseline_len} bytes")
        except:
            print(f"{Fore.RED}[!] Failed to connect to target.{Style.RESET_ALL}")
            self.baseline_resp = None

        # Database Error Signatures (Error Leakage)
        self.error_patterns = [
            "You have an error in your SQL syntax",
            "Warning: mysql_fetch",
            "Unclosed quotation mark",
            "quoted string not properly terminated",
            "Oracle error",
            "SQLServer JDBC Driver"
        ]

    # 1.2 INPUT MUTATION ENGINE (TIERED)
    def get_mutations(self, original_value):
        """
        Menghasilkan payload minimal intrusif berdasarkan tipe data asli.
        """
        mutations = []
        
        # TIER 1: Syntax Breakers (Karakter Kutip)
        # Tujuannya: Memancing syntax error
        mutations.append(({'type': 'T1', 'payload': "'"}, "Single Quote"))
        mutations.append(({'type': 'T1', 'payload': '"'}, "Double Quote"))
        mutations.append(({'type': 'T1', 'payload': "\\"}, "Backslash Escape"))

        # TIER 2: Comment Injection
        # Tujuannya: Memotong query sisa
        mutations.append(({'type': 'T2', 'payload': "'--"}, "Comment Dash"))
        mutations.append(({'type': 'T2', 'payload': "'#"}, "Comment Hash"))

        # TIER 3: Boolean Logic (True/False Tests)
        # Tujuannya: Mengecek Blind SQLi (Perubahan konten)
        # Jika nilai asli angka (misal id=1)
        if original_value.isdigit():
            mutations.append(({'type': 'T3', 'payload': " AND 1=1"}, "Boolean TRUE"))
            mutations.append(({'type': 'T3', 'payload': " AND 1=0"}, "Boolean FALSE"))
        else:
            # Jika string
            mutations.append(({'type': 'T3', 'payload': "' AND 'a'='a"}, "Boolean TRUE"))
            mutations.append(({'type': 'T3', 'payload': "' AND 'a'='b"}, "Boolean FALSE"))
            
        return mutations

    # 1.3 BEHAVIORAL COMPARISON (DIFFING)
    def compare_responses(self, attack_resp):
        """
        Membandingkan respon serangan dengan baseline normal.
        """
        # Cek Perubahan Status Code
        status_diff = attack_resp.status_code != self.baseline_code
        
        # Cek Perubahan Ukuran Konten (Response Size Delta)
        len_diff = abs(len(attack_resp.text) - self.baseline_len)
        
        # Cek Kesamaan Struktural (HTML Similarity Ratio)
        # Menggunakan difflib untuk melihat seberapa mirip HTML-nya
        matcher = difflib.SequenceMatcher(None, self.baseline_resp.text, attack_resp.text)
        similarity = matcher.ratio() # 1.0 = sama persis, 0.0 = beda total
        
        # Cek Error Leakage
        found_error = None
        for err in self.error_patterns:
            if err in attack_resp.text:
                found_error = err
                break
                
        return status_diff, len_diff, similarity, found_error

    # 1.4 SENSITIVITY SCORING
    def calculate_score(self, status_diff, len_diff, similarity, error_msg, mutation_type):
        score = 0
        details = []

        # Skor A: Error Leakage (Paling Fatal)
        if error_msg:
            score += 100
            details.append(f"{Fore.RED}SQL Error Exposed: '{error_msg}'")

        # Skor B: Status Code Shift (misal 200 jadi 500)
        if status_diff:
            score += 40
            details.append(f"{Fore.YELLOW}HTTP Status Shift")

        # Skor C: Boolean Logic Anomaly
        # Jika kita kirim "AND 1=1" (True) responnya mirip baseline -> Score kecil
        # Jika kita kirim "AND 1=0" (False) responnya BEDA JAUH dari baseline -> Score TINGGI (Blind SQLi detected)
        if mutation_type == 'Boolean FALSE' and similarity < 0.95:
            score += 80
            details.append(f"{Fore.RED}Boolean Blind Logic Confirmed")
        elif mutation_type == 'Boolean TRUE' and similarity < 0.90:
             # Seharusnya True itu mirip baseline, kalau beda berarti query rusak
            score += 20 
            details.append(f"{Fore.YELLOW}Query Structure Broken")

        # Skor D: Significant Content Change (Tanpa error)
        if similarity < 0.85 and not status_diff:
            score += 30
            details.append(f"{Fore.MAGENTA}Content Mutated significantly ({int(similarity*100)}% match)")

        return score, details

    def run(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: SQLi Heuristic Engine (Behavioral Analysis){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        if not self.baseline_resp:
            return

        if not self.params:
            print(f"{Fore.RED}[!] No GET parameters found to test.{Style.RESET_ALL}")
            print(f"    Tip: Use Spider first or provide URL like: site.com?id=1")
            return

        print(f"{Fore.YELLOW}[+] Detected Parameters: {', '.join(self.params.keys())}")
        print("-" * 70)

        total_vulns = 0

        # Loop setiap parameter (id, cat, search, dll)
        for param, values in self.params.items():
            original_val = values[0] # Ambil nilai pertama
            print(f"\n{Fore.WHITE}>>> Testing Parameter: {Fore.GREEN}'{param}' {Fore.WHITE}(Original: {original_val})")
            
            mutations = self.get_mutations(original_val)
            
            # Loop setiap mutasi (T1, T2, T3)
            for mutation_data, desc in mutations:
                tier = mutation_data['type']
                payload = mutation_data['payload']
                
                # Clone params biar gak ngerusak loop utama
                attack_params = copy.deepcopy(self.params)
                
                # INJECT PAYLOAD: Original + Mutation
                # Contoh: id=1'
                attack_params[param] = [original_val + payload]
                
                # Reconstruct URL
                query_string = urllib.parse.urlencode(attack_params, doseq=True)
                attack_url = f"{self.base_url}?{query_string}"
                
                try:
                    # Kirim Request Attack
                    attack_resp = requests.get(attack_url, headers=self.headers, timeout=5)
                    
                    # Analisis Behavioral
                    status_chg, len_chg, sim_ratio, error_found = self.compare_responses(attack_resp)
                    
                    # Hitung Skor Sensitivitas
                    score, reasons = self.calculate_score(status_chg, len_chg, sim_ratio, error_found, desc)
                    
                    # Tampilkan jika Skor Signifikan (> 30)
                    if score > 0:
                        level_color = Fore.WHITE
                        if score >= 80: level_color = Fore.RED + "[CRITICAL]"
                        elif score >= 50: level_color = Fore.YELLOW + "[HIGH]"
                        elif score >= 30: level_color = Fore.CYAN + "[MEDIUM]"
                        else: level_color = Fore.WHITE + "[INFO]"

                        if score >= 30: # Filter hanya yang penting
                            print(f"   {level_color} Sensitivity Score: {score}/100 | Method: {desc} ({tier})")
                            print(f"   ├── Payload : {original_val}{Fore.RED}{payload}{Style.RESET_ALL}")
                            print(f"   ├── Changes : Sim={int(sim_ratio*100)}% | SizeDelta={len_chg}b | Status={attack_resp.status_code}")
                            for r in reasons:
                                print(f"   └── Analysis: {r}")
                            
                            if score >= 50:
                                total_vulns += 1
                                
                except requests.exceptions.RequestException:
                    pass
        
        print("-" * 70)
        if total_vulns > 0:
            print(f"{Fore.RED}[!] RESULT: Found {total_vulns} highly suspicious parameters likely vulnerable to SQLi.")
        else:
            print(f"{Fore.GREEN}[OK] Target appears stable against heuristic mutations.")

def run_sqli_scan(url):
    engine = SQLHeuristicEngine(url)
    engine.run()