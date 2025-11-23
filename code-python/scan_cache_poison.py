import requests
import random
import string
import time
from colorama import Fore, Style

class CachePoisonHunter:
    def __init__(self, target_url):
        self.target = target_url.split("?")[0] # Hapus parameter lama
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-CacheHunter/39.0'}
        
        # Header yang sering menyebabkan Cache Poisoning (Unkeyed Inputs)
        self.poison_headers = [
            "X-Forwarded-Host",
            "X-Host",
            "X-Forwarded-Server",
            "X-Original-URL",
            "X-Rewrite-URL",
            "X-Forwarded-Scheme",
            "X-Forwarded-Proto",
            "X-Forwarded-Prefix",
            "X-Amz-Website-Redirect-Location"
        ]
        
        self.canary = "zeroburst_alert" # String unik untuk deteksi refleksi

    def generate_cache_buster(self):
        """Membuat parameter acak agar tidak merusak cache asli user lain"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    def check_header_reflection(self):
        """Mengecek apakah server merefleksikan header inputan (Prasyarat Poisoning)"""
        print(f"\n{Fore.YELLOW}[+] Testing for Unkeyed Header Reflection...{Style.RESET_ALL}")
        
        potential_vulns = []

        for header in self.poison_headers:
            # Kita gunakan Cache Buster agar request kita dianggap "Baru" oleh CDN
            cb = self.generate_cache_buster()
            target_with_cb = f"{self.target}?cb={cb}"
            
            # Payload Header
            # Kita coba inject canary value
            headers = {header: self.canary}
            
            try:
                res = self.session.get(target_with_cb, headers=headers, timeout=5)
                
                # ANALISIS: Apakah canary kita muncul di Body atau Header respon?
                # Jika muncul, berarti server menggunakan input kita untuk men-generate konten.
                # Karena header ini biasanya tidak masuk Cache Key, ini POTENSI POISONING.
                
                is_reflected = False
                location = ""
                
                # Cek Refleksi di Body
                if self.canary in res.text:
                    is_reflected = True
                    location = "Response Body"
                
                # Cek Refleksi di Header (Misal Location: ...)
                for h_name, h_val in res.headers.items():
                    if self.canary in h_val:
                        is_reflected = True
                        location = f"Header ({h_name})"
                        break
                
                if is_reflected:
                    print(f"   {Fore.RED}[VULNERABLE] Reflected Header Found!{Style.RESET_ALL}")
                    print(f"   ├── Header   : {Fore.YELLOW}{header}{Style.RESET_ALL}")
                    print(f"   ├── Location : {location}")
                    print(f"   └── Impact   : High (Cache Poisoning via {header})")
                    potential_vulns.append(header)
                else:
                    # print(f"   [Safe] {header} not reflected.")
                    pass

            except Exception as e:
                pass
        
        return potential_vulns

    def check_cache_headers(self):
        """Mengecek apakah endpoint ini di-cache oleh CDN"""
        print(f"\n{Fore.YELLOW}[+] Analyzing Cache Headers...{Style.RESET_ALL}")
        cb = self.generate_cache_buster()
        url = f"{self.target}?cb={cb}"
        
        try:
            res = self.session.get(url, timeout=5)
            headers = res.headers
            
            cache_indicators = {
                'CF-Cache-Status': 'Cloudflare',
                'X-Cache': 'General CDN',
                'X-Drupal-Cache': 'Drupal',
                'X-Varnish': 'Varnish',
                'Akamai-Cache-Status': 'Akamai'
            }
            
            found = False
            for key, vendor in cache_indicators.items():
                if key in headers:
                    val = headers[key]
                    color = Fore.GREEN
                    if val.upper() in ['HIT', 'MISS', 'DYNAMIC']: color = Fore.CYAN
                    print(f"   ├── {vendor} : {key} = {color}{val}{Style.RESET_ALL}")
                    found = True
            
            if not found:
                print(f"   {Fore.WHITE}[-] No obvious cache headers found.{Style.RESET_ALL}")
                
        except:
            pass

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Web Cache Poisoning Hunter{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[*] Safety: Using Cache Busters (safe for live targets)")
        
        # 1. Cek status Cache
        self.check_cache_headers()
        
        # 2. Cek Vulnerability
        vulns = self.check_header_reflection()
        
        print("-" * 60)
        if vulns:
            print(f"{Fore.RED}[!!!] SCAN COMPLETE: {len(vulns)} Potential Cache Poisoning Vectors found.{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Action: Verify manually if the response is actually cached (HIT).")
        else:
            print(f"{Fore.GREEN}[OK] Target appears safe (No unkeyed input reflection detected).{Style.RESET_ALL}")

def run_cache_scan(url):
    engine = CachePoisonHunter(url)
    engine.run_scan()