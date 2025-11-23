import requests
import urllib.parse
from colorama import Fore, Style

class CORSHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-CORSAuditor/40.0'}
        self.base_origin = "http://zeroburst-audit.com"

    def check_configuration(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: CORS Misconfiguration Auditor{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        # Test Cases
        scenarios = [
            {
                'name': 'Reflected Origin (Basic)',
                'origin': 'http://evil.com',
                'desc': 'Server trusts arbitrary domains.'
            },
            {
                'name': 'Trust Null Origin',
                'origin': 'null',
                'desc': 'Server trusts sandboxed iframes/local files.'
            },
            {
                'name': 'Pre-domain Wildcard',
                'origin': f'http://evil{urllib.parse.urlparse(self.target).netloc}',
                'desc': 'Weak Regex (prefix match).'
            },
            {
                'name': 'Post-domain Wildcard',
                'origin': f'http://{urllib.parse.urlparse(self.target).netloc}.evil.com',
                'desc': 'Weak Regex (suffix match).'
            }
        ]

        vuln_found = 0

        for case in scenarios:
            print(f"\n{Fore.WHITE}>>> Testing: {case['name']}...{Style.RESET_ALL}")
            
            try:
                headers = {'Origin': case['origin']}
                # Kirim request dengan Origin palsu
                res = self.session.get(self.target, headers=headers, timeout=5)
                
                # Analisis Header Respons
                allow_origin = res.headers.get('Access-Control-Allow-Origin', '')
                allow_creds = res.headers.get('Access-Control-Allow-Credentials', 'false')
                
                is_vuln = False
                severity = "LOW"
                
                # Cek apakah Origin kita diterima
                if allow_origin and (allow_origin == case['origin'] or allow_origin == '*'):
                    is_vuln = True
                    
                    # Jika Credentials: true, ini Critical karena Cookie/Token bisa dicuri
                    if allow_creds.lower() == 'true':
                        severity = "CRITICAL"
                        note = "Cookies/Auth Tokens can be exfiltrated!"
                    else:
                        severity = "MEDIUM"
                        note = "Data can be read, but no cookies sent."

                if is_vuln:
                    print(f"   {Fore.RED}[VULNERABLE] Misconfiguration Detected!{Style.RESET_ALL}")
                    print(f"   ├── Severity  : {severity}")
                    print(f"   ├── Payload   : Origin: {case['origin']}")
                    print(f"   ├── Response  : ACAO: {allow_origin} | ACAC: {allow_creds}")
                    print(f"   └── Impact    : {note}")
                    vuln_found += 1
                else:
                    print(f"   {Fore.GREEN}[SAFE] Server rejected origin '{case['origin']}'{Style.RESET_ALL}")

            except Exception as e:
                # print(e)
                pass

        print("-" * 60)
        if vuln_found > 0:
            print(f"{Fore.RED}[!!!] AUDIT COMPLETE: {vuln_found} CORS misconfigurations found.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[OK] AUDIT COMPLETE: CORS policy appears strict.{Style.RESET_ALL}")

def run_cors_scan(url):
    engine = CORSHunter(url)
    engine.check_configuration()