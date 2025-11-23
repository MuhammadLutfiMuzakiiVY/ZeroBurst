import requests
import concurrent.futures
from bs4 import BeautifulSoup
from colorama import Fore, Style

class CMSHunter:
    def __init__(self, target_url):
        self.target = target_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-CMSHunter/31.0'}
        
        # DATABASE PLUGIN/THEME RENTAN (Sample Top Critical)
        self.wp_plugins = [
            "elementor", "woocommerce", "contact-form-7", "wp-file-manager",
            "slider-revolution", "layer-slider", "w3-total-cache", "wordfence",
            "all-in-one-seo-pack", "wp-super-cache", "duplicator", "updraftplus"
        ]
        
        self.joomla_components = [
            "com_akeeba", "com_jce", "com_virtuemart", "com_rsform", "com_k2"
        ]

    def detect_cms(self):
        """Mendeteksi jenis CMS berdasarkan ciri khas"""
        print(f"\n{Fore.YELLOW}[+] Detecting CMS Type...{Style.RESET_ALL}")
        try:
            res = self.session.get(self.target, timeout=10)
            html = res.text.lower()
            
            if "wp-content" in html or "wp-includes" in html:
                return "WordPress"
            elif "content=\"joomla" in html or "/templates/" in html and "joomla" in html:
                return "Joomla"
            elif "drupal.settings" in html or "sites/default/files" in html:
                return "Drupal"
            
            # Cek Meta Generator
            soup = BeautifulSoup(html, 'html.parser')
            meta = soup.find("meta", attrs={"name": "generator"})
            if meta:
                content = meta.get("content", "").lower()
                if "wordpress" in content: return "WordPress"
                if "joomla" in content: return "Joomla"
                if "drupal" in content: return "Drupal"
                
        except:
            pass
        return None

    def scan_wordpress(self):
        print(f"{Fore.CYAN}[*] Starting Deep WordPress Scan...{Style.RESET_ALL}")
        
        # 1. User Enumeration (REST API)
        print(f"   {Fore.WHITE}├── Checking User Enumeration (REST API)...")
        try:
            api_url = f"{self.target}/wp-json/wp/v2/users"
            res = self.session.get(api_url, timeout=5)
            if res.status_code == 200:
                users = res.json()
                print(f"   {Fore.RED}└── [VULNERABLE] Users Found:{Style.RESET_ALL}")
                for u in users:
                    print(f"       - ID: {u['id']} | User: {Fore.GREEN}{u['slug']}{Style.RESET_ALL} | Name: {u['name']}")
            else:
                print(f"   └── [SAFE] REST API User Enum blocked.")
        except:
            pass

        # 2. Critical Files & Config Backups
        files = ["license.txt", "readme.html", "wp-config.php.bak", "wp-config.php.save", ".htaccess"]
        print(f"   {Fore.WHITE}├── Checking Exposed Core Files...")
        for f in files:
            url = f"{self.target}/{f}"
            res = self.session.get(url, timeout=5)
            if res.status_code == 200:
                print(f"   {Fore.YELLOW}└── [EXPOSED] {url} (Check for version info){Style.RESET_ALL}")

        # 3. Plugin Enumeration (Heuristic)
        print(f"   {Fore.WHITE}├── Enumerating Top Risky Plugins...")
        for plugin in self.wp_plugins:
            # Cek folder readme plugin
            url = f"{self.target}/wp-content/plugins/{plugin}/readme.txt"
            res = self.session.get(url, timeout=3)
            if res.status_code == 200:
                # Coba ambil versi dari readme
                version = "Unknown"
                for line in res.text.splitlines()[:30]:
                    if "Stable tag:" in line:
                        version = line.split(":")[1].strip()
                        break
                print(f"   {Fore.RED}└── [FOUND] Plugin: {plugin} (Version: {version}){Style.RESET_ALL}")

    def scan_joomla(self):
        print(f"{Fore.CYAN}[*] Starting Deep Joomla Scan...{Style.RESET_ALL}")
        
        # 1. Config & Manifests
        files = ["configuration.php.bak", "configuration.php.dist", "web.config.txt", "htaccess.txt", "administrator/manifests/files/joomla.xml"]
        print(f"   {Fore.WHITE}├── Checking Config & Manifests...")
        for f in files:
            url = f"{self.target}/{f}"
            res = self.session.get(url, timeout=5)
            if res.status_code == 200:
                info = ""
                if "joomla.xml" in f:
                    # Coba regex versi
                    import re
                    ver = re.search(r'<version>(.*?)</version>', res.text)
                    if ver: info = f"(Version: {ver.group(1)})"
                print(f"   {Fore.RED}└── [EXPOSED] {url} {info}{Style.RESET_ALL}")

        # 2. Component Scanner
        print(f"   {Fore.WHITE}├── Checking Common Components...")
        for comp in self.joomla_components:
            url = f"{self.target}/components/{comp}/"
            res = self.session.get(url, timeout=3)
            if res.status_code in [200, 403]: # 403 means folder exists but forbidden
                print(f"   {Fore.YELLOW}└── [FOUND] Component: {comp}{Style.RESET_ALL}")

    def scan_drupal(self):
        print(f"{Fore.CYAN}[*] Starting Deep Drupal Scan...{Style.RESET_ALL}")
        
        # 1. Version Disclosure
        files = ["CHANGELOG.txt", "README.txt", "INSTALL.txt", "sites/default/settings.php.bak"]
        print(f"   {Fore.WHITE}├── Checking Core Files...")
        for f in files:
            url = f"{self.target}/{f}"
            res = self.session.get(url, timeout=5)
            if res.status_code == 200:
                # Drupal CHANGELOG.txt sering bocor versi paling atas
                ver = ""
                if "CHANGELOG" in f:
                    line = res.text.splitlines()[0:5]
                    for l in line:
                        if "Drupal" in l: ver = f"({l.strip()})"
                
                print(f"   {Fore.RED}└── [EXPOSED] {url} {ver}{Style.RESET_ALL}")

        # 2. User Login Page Check
        res = self.session.get(f"{self.target}/user/login", timeout=5)
        if res.status_code == 200:
            print(f"   {Fore.GREEN}└── Admin Login Found: {self.target}/user/login{Style.RESET_ALL}")

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: CMS Vulnerability Hunter{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        cms_type = self.detect_cms()
        
        if cms_type == "WordPress":
            print(f"{Fore.GREEN}[+] CMS Detected: WordPress{Style.RESET_ALL}")
            self.scan_wordpress()
        elif cms_type == "Joomla":
            print(f"{Fore.GREEN}[+] CMS Detected: Joomla{Style.RESET_ALL}")
            self.scan_joomla()
        elif cms_type == "Drupal":
            print(f"{Fore.GREEN}[+] CMS Detected: Drupal{Style.RESET_ALL}")
            self.scan_drupal()
        else:
            print(f"{Fore.RED}[-] No Supported CMS Detected (WP/Joomla/Drupal).{Style.RESET_ALL}")
            print(f"    Skipping specific CMS scan.")

        print("-" * 60)

def run_cms_scan(url):
    engine = CMSHunter(url)
    engine.run_scan()