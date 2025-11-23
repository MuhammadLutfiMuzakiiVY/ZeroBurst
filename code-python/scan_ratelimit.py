import requests
import time
import random
from colorama import Fore, Style

class RateLimitAuditor:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-RateLimitAuditor/45.0'}
        
        # Header yang sering disalahgunakan untuk bypass IP-based Limiting
        self.spoof_headers = [
            "X-Forwarded-For",
            "X-Real-IP",
            "X-Client-IP",
            "X-Originating-IP",
            "X-Remote-IP",
            "X-Remote-Addr",
            "Client-IP"
        ]

    def generate_random_ip(self):
        """Membuat IP acak palsu"""
        return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

    def check_header_trust(self):
        """
        Mengecek apakah server mempercayai header IP palsu untuk Rate Limiting.
        Metode:
        1. Kirim Request A (IP Palsu 1).
        2. Kirim Request B (IP Palsu 2).
        3. Bandingkan Header 'X-RateLimit-Remaining'.
        
        Jika kuota Request B tidak berkurang dari Request A, berarti server
        menganggap mereka user berbeda (VULNERABLE CONFIGURATION).
        """
        print(f"\n{Fore.CYAN}[*] MODULE START: Rate Limit Configuration Auditor{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[*] Method: Header Trust Analysis (Diagnostic)")
        print("-" * 60)

        # Baseline Request (Tanpa spoofing)
        try:
            res_base = self.session.get(self.target, timeout=5)
            limit_header = None
            
            # Cari header indikator limit
            for h in res_base.headers:
                if "ratelimit" in h.lower() and "remaining" in h.lower():
                    limit_header = h
                    print(f"{Fore.YELLOW}[INFO] Rate Limit Header Detected: {h} = {res_base.headers[h]}{Style.RESET_ALL}")
                    break
            
            if not limit_header:
                print(f"{Fore.WHITE}[-] No standard 'X-RateLimit-Remaining' header found.")
                print(f"    analysis will rely on status codes (429 Too Many Requests).")

        except:
            print(f"{Fore.RED}[!] Connection Error.{Style.RESET_ALL}")
            return

        # Audit Loop
        print(f"\n{Fore.YELLOW}[+] Testing Header Trust Issues...{Style.RESET_ALL}")
        
        for header in self.spoof_headers:
            # Simulasi 2 User berbeda dengan header yang sama
            ip1 = self.generate_random_ip()
            ip2 = self.generate_random_ip()
            
            headers1 = {header: ip1}
            headers2 = {header: ip2}
            
            try:
                # Request 1
                r1 = self.session.get(self.target, headers=headers1, timeout=5)
                rem1 = r1.headers.get(limit_header) if limit_header else "N/A"
                
                # Request 2
                r2 = self.session.get(self.target, headers=headers2, timeout=5)
                rem2 = r2.headers.get(limit_header) if limit_header else "N/A"
                
                # Analisis
                # Jika Rate Limit dihitung per-IP (berdasarkan header palsu kita), 
                # maka rem1 dan rem2 harusnya mirip/tinggi (karena IP baru).
                # Jika Rate Limit Global (IP asli kita), maka rem2 harusnya lebih kecil dari rem1.
                
                print(f"   Testing {header:<20} -> IP1: {rem1} | IP2: {rem2}")
                
                # Logika Deteksi Sederhana (Indikatif)
                if r1.status_code == 429 and r2.status_code == 200:
                     print(f"      {Fore.RED}[VULNERABLE] Bypass Successful! {header} resets the limit.{Style.RESET_ALL}")
                elif limit_header and rem1 == rem2 and rem1 != "N/A":
                     print(f"      {Fore.RED}[VULNERABLE] Quota did not decrease. Server trusts {header}.{Style.RESET_ALL}")

            except:
                pass

        print("-" * 60)
        print(f"{Fore.CYAN}[*] Audit Completed.{Style.RESET_ALL}")

def run_ratelimit_scan(url):
    engine = RateLimitAuditor(url)
    engine.check_header_trust()