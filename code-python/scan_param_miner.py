import requests
import re
import urllib.parse
from bs4 import BeautifulSoup
from colorama import Fore, Style

class ParameterMiner:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-ParamMiner/25.0'}
        self.base_url = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(target_url))

    def analyze_url_query(self):
        """Mendeteksi parameter yang ada di URL (GET Params)"""
        parsed = urllib.parse.urlparse(self.target)
        params = urllib.parse.parse_qs(parsed.query)
        
        if params:
            print(f"\n{Fore.YELLOW}[+] URL Query Parameters Detected:{Style.RESET_ALL}")
            for p, v in params.items():
                print(f"   ├── Name  : {Fore.CYAN}{p}{Style.RESET_ALL}")
                print(f"   └── Value : {v[0]}")
        else:
            print(f"\n{Fore.WHITE}[-] No URL Query parameters detected (Clean URL).")

    def analyze_forms(self, soup):
        """Mendeteksi Form HTML (Login, Search, Register)"""
        forms = soup.find_all('form')
        print(f"\n{Fore.YELLOW}[+] HTML Form Analysis ({len(forms)} found):{Style.RESET_ALL}")
        
        for i, form in enumerate(forms):
            action = form.get('action') or self.target
            method = form.get('method', 'get').upper()
            
            # Fix relative URL
            if not action.startswith('http'):
                action = urllib.parse.urljoin(self.target, action)
            
            # Tebak Jenis Form
            form_type = "Generic Form"
            form_html = str(form).lower()
            if "login" in form_html or "sign in" in form_html: form_type = "LOGIN Portal"
            elif "search" in form_html or "cari" in form_html: form_type = "SEARCH Bar"
            elif "register" in form_html or "sign up" in form_html: form_type = "REGISTER Page"
            elif "upload" in form_html: form_type = "FILE UPLOAD"

            print(f"\n   {Fore.MAGENTA}[Form #{i+1}] Type: {form_type}{Style.RESET_ALL}")
            print(f"   ├── Method : {method}")
            print(f"   ├── Action : {action}")
            print(f"   └── Inputs :")
            
            inputs = form.find_all(['input', 'textarea', 'select', 'button'])
            for inp in inputs:
                i_name = inp.get('name')
                i_type = inp.get('type', 'text')
                i_id = inp.get('id')
                
                if i_name:
                    color = Fore.WHITE
                    if i_type == 'password': color = Fore.RED # High Value
                    elif i_type == 'hidden': color = Fore.YELLOW # Interesting
                    elif i_type == 'file': color = Fore.CYAN # Upload Vuln Potential
                    
                    print(f"       - Name: {color}{i_name:<15}{Style.RESET_ALL} | Type: {i_type:<8} | ID: {i_id}")

    def analyze_api_endpoints(self, content):
        """Mencari pola API di dalam Source Code (Regex)"""
        print(f"\n{Fore.YELLOW}[+] API & AJAX Endpoint Discovery (Regex Heuristic):{Style.RESET_ALL}")
        
        # Regex untuk menangkap /api/v1/..., .json, .xml di dalam JS
        # Pola: String yang diawali / atau http, mengandung 'api' atau ekstensi data
        patterns = [
            r"['\"](\/api\/.*?)['\"]",
            r"['\"](\/v\d\/.*?)['\"]",
            r"['\"](https?:\/\/.*?\/api\/.*?)['\"]",
            r"['\"](.*?.json)['\"]",
            r"['\"](.*?.php\?.*?)['\"]" # Endpoint PHP dengan parameter
        ]
        
        found_apis = set()
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                if len(m) > 4 and " " not in m:
                    found_apis.add(m)
        
        if found_apis:
            for api in found_apis:
                print(f"   ├── {Fore.GREEN}{api}{Style.RESET_ALL}")
        else:
            print(f"   {Fore.WHITE}[-] No obvious API endpoints found in source code.")

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Parameter & Form Miner (Input Discovery){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        print("-" * 60)

        try:
            res = self.session.get(self.target, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 1. URL Params
            self.analyze_url_query()
            
            # 2. Forms
            self.analyze_forms(soup)
            
            # 3. API Extraction
            self.analyze_api_endpoints(res.text)
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error connecting: {e}")

        print("-" * 60)
        print(f"{Fore.GREEN}[*] Mining Completed. Use these inputs for SQLi/XSS modules.{Style.RESET_ALL}")

def run_miner(url):
    engine = ParameterMiner(url)
    engine.run_scan()