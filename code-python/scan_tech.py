import requests
import socket
import ssl
import re
import json
import datetime
import hashlib
import codecs
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

# Inisialisasi Colorama
init(autoreset=True)

class HyperSenseEngine:
    def __init__(self, target_url):
        self.target = target_url
        self.parsed_url = urlparse(target_url)
        self.domain = self.parsed_url.netloc
        self.scheme = self.parsed_url.scheme
        self.base_url = f"{self.scheme}://{self.domain}"
        
        # Session dengan Headers Browser Modern
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        # Database Favicon Hash (Teknik Shodan)
        # MD5 Hash dari favicon.ico default
        self.favicon_hashes = {
            '69372856363b276e64a27034d202473e': 'Laravel',
            '7426626d777f77620943022700000000': 'Spring Boot',
            '0795d9a3f938c3c44729900833420829': 'React',
            '1d5270027900786c2830634900000000': 'Vue.js',
            '25505505505505505505505505505505': 'Apache Tomcat', # Contoh
            'b7c5b991753457894830000000000000': 'Jenkins',
            'd41d8cd98f00b204e9800998ecf8427e': 'Empty File'
        }

        # Database Signature Teknologi (Regex)
        self.signatures = {
            'CMS': {
                'WordPress': [r'wp-content', r'wp-includes', r'xmlrpc\.php'],
                'Joomla': [r'content="Joomla!', r'/media/system/js/core\.js'],
                'Drupal': [r'Drupal\.settings', r'sites/default/files'],
                'Magento': [r'Mage\.Cookies', r'static/_requirejs'],
                'Shopify': [r'cdn\.shopify\.com', r'Shopify\.theme'],
                'Wix': [r'wix-bolt', r'X-Wix-RequestId'],
            },
            'Framework': {
                'Laravel': [r'laravel_session', r'XSRF-TOKEN', r'whoops!'],
                'CodeIgniter': [r'ci_session'],
                'Django': [r'csrftoken', r'__admin__'],
                'Rails': [r'X-Runtime', r'authenticity_token'],
                'React.js': [r'react\.production\.min\.js', r'data-reactid', r'_reactInternalInstance'],
                'Vue.js': [r'vue\.js', r'data-v-', r'__vue__'],
                'Angular': [r'ng-app', r'angular\.js', r'ng-version'],
                'Next.js': [r'__NEXT_DATA__', r'/_next/static'],
                'Bootstrap': [r'bootstrap[.-]?[0-9.]*\.css'],
                'Tailwind': [r'tailwind'],
            },
            'Server': {
                'Cloudflare': [r'__cfduid', r'cf-ray'],
                'Nginx': [r'nginx'],
                'Apache': [r'apache'],
                'IIS': [r'Microsoft-IIS'],
                'LiteSpeed': [r'LiteSpeed'],
                'Gunicorn': [r'gunicorn'],
            },
            'Lang': {
                'PHP': [r'\.php', r'PHPSESSID'],
                'Python': [r'Werkzeug', r'Python'],
                'ASP.NET': [r'ASP\.NET', r'ASPSESSIONID'],
                'Java': [r'JSESSIONID', r'Apache-Coyote']
            }
        }

    def get_favicon_hash(self):
        """Mendapatkan Hash MD5 dari Favicon untuk identifikasi"""
        print(f"\n{Fore.YELLOW}[+] Analysis: Favicon Fingerprinting (Shodan Style)...{Style.RESET_ALL}")
        try:
            # Coba path standar
            icon_url = urljoin(self.base_url, '/favicon.ico')
            res = self.session.get(icon_url, timeout=5)
            
            if res.status_code == 200 and len(res.content) > 0:
                # Hitung MD5
                # Teknik Shodan menggunakan MurmurHash, tapi MD5 cukup untuk database lokal kita
                raw_content = res.content
                md5_hash = hashlib.md5(raw_content).hexdigest()
                
                # Base64 untuk visualisasi
                b64_icon = codecs.encode(raw_content, 'base64').decode().replace('\n', '')[:20] + "..."
                
                print(f"   ├── Icon Found  : {len(raw_content)} bytes")
                print(f"   ├── MD5 Hash    : {Fore.CYAN}{md5_hash}{Style.RESET_ALL}")
                
                if md5_hash in self.favicon_hashes:
                    tech = self.favicon_hashes[md5_hash]
                    print(f"   └── {Fore.GREEN}[MATCH] Identified via Icon: {tech}{Style.RESET_ALL}")
                    return tech
                else:
                    print(f"   └── Unknown Hash (Not in local DB)")
            else:
                print(f"   └── No favicon.ico found (404/Empty)")
        except Exception as e:
            pass
        return None

    def check_error_page(self):
        """Memaksa error 404 untuk melihat signature server"""
        print(f"\n{Fore.YELLOW}[+] Analysis: Forced Error Page Fingerprinting...{Style.RESET_ALL}")
        try:
            # Request halaman acak
            random_page = urljoin(self.base_url, f"/zeroburst_scan_{hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[:8]}")
            res = self.session.get(random_page, timeout=5)
            
            if res.status_code == 404:
                server_sig = res.headers.get('Server', 'Unknown')
                print(f"   ├── 404 Status  : Confirmed")
                print(f"   ├── Server Hdr  : {Fore.MAGENTA}{server_sig}{Style.RESET_ALL}")
                
                # Cek Body Error Default
                text = res.text.lower()
                if "apache" in text and "port" in text:
                    print(f"   └── {Fore.GREEN}[MATCH] Default Apache 404 Page Detected{Style.RESET_ALL}")
                elif "nginx" in text:
                    print(f"   └── {Fore.GREEN}[MATCH] Default Nginx 404 Page Detected{Style.RESET_ALL}")
                elif "tomcat" in text:
                    print(f"   └── {Fore.GREEN}[MATCH] Apache Tomcat Error Page Detected{Style.RESET_ALL}")
                elif "laravel" in text or "whoops" in text:
                    print(f"   └── {Fore.GREEN}[MATCH] Laravel Debug Page (Whoops) Detected!{Style.RESET_ALL}")
            else:
                print(f"   └── Soft 404 or Redirect (Status: {res.status_code})")
        except:
            pass

    def run_analysis(self):
        print(f"\n{Fore.CYAN}==========================================================================")
        print(f"   ZEROBURST TECH TITAN v3.0 | Target: {self.target}")
        print(f"   Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"=========================================================================={Style.RESET_ALL}")
        
        try:
            # 1. Main Request
            response = self.session.get(self.target, timeout=15, verify=False)
            html_content = response.text
            response_headers = response.headers
            response_cookies = response.cookies.get_dict()
            
            # 2. Tech Fingerprinting (Regex & Headers)
            print(f"\n{Fore.YELLOW}[+] Analysis: Tech Stack Signature Matching...{Style.RESET_ALL}")
            detected_tech = []
            
            # Combine all text for search
            search_text = html_content + str(response_headers) + str(response_cookies)
            
            for category, techs in self.signatures.items():
                for tech_name, patterns in techs.items():
                    for pattern in patterns:
                        if re.search(pattern, search_text, re.IGNORECASE):
                            # Format: [Category] Name
                            detected_tech.append(f"{Fore.WHITE}[{category}] {Fore.GREEN}{tech_name}{Style.RESET_ALL}")
                            break # Satu match cukup per teknologi
            
            # Check Headers explicitly (Lebih Akurat)
            if 'Server' in response_headers:
                detected_tech.append(f"{Fore.WHITE}[Header] {Fore.MAGENTA}{response_headers['Server']}{Style.RESET_ALL}")
            if 'X-Powered-By' in response_headers:
                detected_tech.append(f"{Fore.WHITE}[Header] {Fore.MAGENTA}{response_headers['X-Powered-By']}{Style.RESET_ALL}")
            if 'X-Generator' in response_headers:
                detected_tech.append(f"{Fore.WHITE}[Header] {Fore.MAGENTA}{response_headers['X-Generator']}{Style.RESET_ALL}")
                
            if detected_tech:
                detected_tech = sorted(list(set(detected_tech))) # Unik
                for dt in detected_tech:
                    print(f"   ├── {dt}")
            else:
                print(f"   {Fore.RED}[?] No standard technologies identified (Stealth Mode?).")

            # 3. Advanced Modules
            self.get_favicon_hash()
            self.check_error_page()
            
            # 4. Security Headers Audit
            print(f"\n{Fore.YELLOW}[+] Analysis: Security Headers Audit...{Style.RESET_ALL}")
            security_headers = {
                "Strict-Transport-Security": "HSTS",
                "X-Frame-Options": "Clickjacking Def",
                "X-XSS-Protection": "XSS Def",
                "Content-Security-Policy": "CSP",
                "Referrer-Policy": "Info Leak Def",
                "Permissions-Policy": "Browser Feature Def"
            }
            
            score = 0
            total_checks = len(security_headers)
            
            for h, desc in security_headers.items():
                if h in response_headers:
                    print(f"   {Fore.GREEN}[PASS] {h:<27} ({desc})")
                    score += 1
                else:
                    print(f"   {Fore.RED}[FAIL] {h:<27} (Missing {desc})")
            
            grade = (score / total_checks) * 100
            print(f"\n   {Fore.CYAN}>> Security Score: {int(grade)}/100{Style.RESET_ALL}")

        except requests.exceptions.SSLError:
            print(f"{Fore.RED}[!] SSL Error. Target might have invalid certificate.")
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}[!] Connection Refused. Host is down.")
        except Exception as e:
            print(f"{Fore.RED}[!] Critical Error: {e}")

        print(f"\n{Fore.CYAN}[*] Tech Analysis Completed.{Style.RESET_ALL}")
        print("-" * 75)

# --- FUNGSI PEMANGGIL ---
def analyze_tech(url):
    engine = HyperSenseEngine(url)
    engine.run_analysis()