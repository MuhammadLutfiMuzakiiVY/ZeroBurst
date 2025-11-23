import requests
import re
import urllib.parse
from bs4 import BeautifulSoup
from collections import deque
from colorama import Fore, Style

class DeepCrawlerEngine:
    def __init__(self, target_url, max_pages=50):
        self.start_url = target_url
        self.base_domain = urllib.parse.urlparse(target_url).netloc
        self.scheme = urllib.parse.urlparse(target_url).scheme
        self.max_pages = max_pages
        
        # Antrian Crawling
        self.queue = deque([target_url])
        self.visited = set()
        
        # Hasil Temuan
        self.found_endpoints = set()
        self.found_params = set()
        self.found_forms = []
        self.found_secrets = set() # Endpoint dari JS

        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-DeepCrawler/24.0'}

    def normalize_url(self, url, base_url):
        """Membersihkan dan menyatukan URL relatif"""
        if not url or url.startswith(('javascript:', 'mailto:', '#')):
            return None
        try:
            full_url = urllib.parse.urljoin(base_url, url)
            parsed = urllib.parse.urlparse(full_url)
            # Pastikan tetap di domain target (Scope Control)
            if parsed.netloc == self.base_domain:
                # Hapus fragment (#)
                return full_url.split('#')[0]
        except:
            pass
        return None

    def extract_forms(self, soup, page_url):
        """Menganalisis Form, Input, dan Hidden Field"""
        forms = soup.find_all('form')
        for form in forms:
            action = form.get('action')
            method = form.get('method', 'GET').upper()
            
            # Normalize action
            form_endpoint = self.normalize_url(action, page_url) or page_url
            
            inputs = []
            for inp in form.find_all(['input', 'textarea', 'select']):
                in_name = inp.get('name')
                in_type = inp.get('type', 'text')
                
                if in_name:
                    detail = f"{in_name}({in_type})"
                    if in_type == 'hidden':
                        detail = f"{Fore.RED}{in_name}(HIDDEN){Style.RESET_ALL}"
                    inputs.append(detail)
            
            form_data = {
                'url': form_endpoint,
                'method': method,
                'inputs': inputs
            }
            
            # Simpan jika belum ada (hindari duplikat)
            if str(form_data) not in [str(f) for f in self.found_forms]:
                self.found_forms.append(form_data)
                print(f"   {Fore.MAGENTA}[FORM DETECTED] {method} {form_endpoint}{Style.RESET_ALL}")
                print(f"   └── Inputs: {', '.join(inputs)}")

    def extract_js_endpoints(self, html_content):
        """Mining endpoint tersembunyi di dalam script JS"""
        # Regex untuk mencari string path (e.g., "/api/v1/user", "admin.php")
        # Pattern: string diawali / atau diakhiri .php/.json, diapit quote
        regex = r"['\"](\/[a-zA-Z0-9_./-]+|[a-zA-Z0-9_./-]+\.php|[a-zA-Z0-9_./-]+\.json)['\"]"
        matches = re.findall(regex, html_content)
        
        for match in matches:
            # Filter junk
            if len(match) > 2 and not match.startswith('//') and ' ' not in match:
                if match not in self.found_secrets:
                    self.found_secrets.add(match)
                    print(f"   {Fore.YELLOW}[JS MINER] Hidden Path Found: {match}{Style.RESET_ALL}")

    def run_crawl(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Deep Website Crawling & Spidering{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.start_url}")
        print(f"{Fore.WHITE}[*] Scope: {self.base_domain} (Max {self.max_pages} Pages)")
        print("-" * 60)

        count = 0
        while self.queue and count < self.max_pages:
            url = self.queue.popleft()
            
            if url in self.visited:
                continue
                
            self.visited.add(url)
            count += 1
            
            # Tampilan Progress
            print(f"{Fore.GREEN}[+] Crawling ({count}/{self.max_pages}): {Fore.WHITE}{url[:60]}...")
            
            try:
                res = self.session.get(url, timeout=5)
                
                # Skip non-text (images, pdf, etc)
                if 'text/html' not in res.headers.get('Content-Type', ''):
                    continue

                # 1. PARSE URL PARAMETERS
                parsed_url = urllib.parse.urlparse(url)
                params = urllib.parse.parse_qs(parsed_url.query)
                for p in params.keys():
                    if p not in self.found_params:
                        self.found_params.add(p)
                        print(f"   {Fore.CYAN}[PARAM] New Parameter Discovered: '{p}'{Style.RESET_ALL}")

                soup = BeautifulSoup(res.text, 'html.parser')

                # 2. EXTRACT FORMS & HIDDEN INPUTS
                self.extract_forms(soup, url)

                # 3. EXTRACT JS HIDDEN ENDPOINTS
                self.extract_js_endpoints(res.text)

                # 4. HARVEST NEW LINKS (SPIDERING)
                for tag in soup.find_all(['a', 'link', 'script', 'iframe']):
                    href = tag.get('href') or tag.get('src')
                    full_link = self.normalize_url(href, url)
                    
                    if full_link and full_link not in self.visited and full_link not in self.queue:
                        # Filter ekstensi statis agar tidak crawl gambar
                        if not full_link.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.ico')):
                            self.queue.append(full_link)
                            self.found_endpoints.add(full_link)

            except Exception as e:
                # print(f"   [!] Error: {e}")
                pass

        # --- SUMMARY REPORT ---
        print("\n" + "=" * 60)
        print(f"{Fore.YELLOW}[CRAWL SUMMARY REPORT]{Style.RESET_ALL}")
        print(f"   ├── Total Pages Scanned : {count}")
        print(f"   ├── Unique Endpoints    : {len(self.found_endpoints)}")
        print(f"   ├── Parameters Found    : {len(self.found_params)} ({', '.join(list(self.found_params)[:10])}...)")
        print(f"   ├── Hidden Inputs Found : Check [FORM DETECTED] logs above")
        print(f"   └── JS Hidden Paths     : {len(self.found_secrets)}")
        print("=" * 60)

def run_deep_crawl(url):
    engine = DeepCrawlerEngine(url)
    engine.run_crawl()