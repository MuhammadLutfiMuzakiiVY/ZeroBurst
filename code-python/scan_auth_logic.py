import requests
import urllib.parse
from colorama import Fore, Style

class AuthLogicAuditor:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-AuthLogic/55.0'}
        self.base_url = target_url.split("?")[0]

    def check_step_skipping(self):
        """
        Mendeteksi potensi 'Forced Browsing' atau Step Skipping.
        Mencoba akses endpoint 'sukses' tanpa login.
        """
        print(f"\n{Fore.YELLOW}[+] Testing for Step Skipping (Broken Access Control)...{Style.RESET_ALL}")
        
        # Endpoint yang seharusnya butuh auth/OTP
        sensitive_paths = [
            "/dashboard", "/admin", "/account", "/profile", 
            "/settings", "/api/users", "/home", "/otp/verify"
        ]
        
        base_domain = "/".join(self.target.split("/")[:3]) # http://site.com
        
        for path in sensitive_paths:
            test_url = f"{base_domain}{path}"
            try:
                res = self.session.get(test_url, timeout=5, allow_redirects=False)
                
                # Jika status 200 OK dan tidak ada indikasi login page, ini mencurigakan
                if res.status_code == 200:
                    if "login" not in res.text.lower() and "signin" not in res.text.lower():
                        print(f"   {Fore.RED}[CRITICAL] DIRECT ACCESS POSSIBLE: {test_url}{Style.RESET_ALL}")
                        print(f"   ├── Status: 200 OK")
                        print(f"   └── Risk  : Endpoint accessible without session/OTP verification.")
                    else:
                        print(f"   {Fore.GREEN}[SAFE] {path} redirects to login or contains login form.{Style.RESET_ALL}")
                elif res.status_code in [301, 302, 401, 403]:
                    print(f"   {Fore.GREEN}[SAFE] {path} is protected ({res.status_code}).{Style.RESET_ALL}")
            except:
                pass

    def check_role_manipulation(self):
        """
        Mengirim parameter role tambahan untuk melihat reaksi server.
        (Indikasi Mass Assignment pada Logic Auth)
        """
        print(f"\n{Fore.YELLOW}[+] Testing Role Parameter Logic...{Style.RESET_ALL}")
        
        # Payload manipulasi role
        payloads = {
            "role": "admin",
            "is_admin": "true",
            "isAdmin": 1,
            "group": "superadmin",
            "type": "1" # Kadang 1 = admin
        }
        
        # Kita coba kirim ini ke URL target (asumsi ini endpoint register/update profile)
        try:
            # Test GET
            res_get = self.session.get(self.target, params=payloads, timeout=5)
            
            # Analisis Respon
            # Jika respon berubah drastis atau menampilkan kata kunci admin, warning.
            if "admin" in res_get.text.lower() and "admin" not in self.target:
                 print(f"   {Fore.MAGENTA}[UNK] Server reflected 'admin' keyword after parameter injection.{Style.RESET_ALL}")
                 print(f"   └── Check manually if role was elevated.")
            
            # Cek Cookie Baru
            for cookie in res_get.cookies:
                if "admin" in cookie.name or "role" in cookie.name:
                     print(f"   {Fore.RED}[HIGH] Server set a cookie named '{cookie.name}' after injection!{Style.RESET_ALL}")

        except:
            pass
        
        print(f"   {Fore.WHITE}[INFO] Role manipulation checks completed.{Style.RESET_ALL}")

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Authentication Logic Auditor{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        self.check_step_skipping()
        self.check_role_manipulation()
        
        print("-" * 60)

def run_auth_logic_scan(url):
    engine = AuthLogicAuditor(url)
    engine.run_scan()