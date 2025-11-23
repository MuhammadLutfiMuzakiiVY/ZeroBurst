import requests
import json
from colorama import Fore, Style

class SupplyChainAuditor:
    def __init__(self, target_url):
        self.target = target_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-SupplyChainAuditor/55.0'}
        
        # Endpoint Registry Publik
        self.registries = {
            'NPM': 'https://registry.npmjs.org/{}',
            'PyPI': 'https://pypi.org/pypi/{}/json',
            'Composer': 'https://repo.packagist.org/p2/{}.json',
            'WordPress': 'https://wordpress.org/plugins/{}/' # Cek halaman plugin
        }

    def check_registry(self, ecosystem, package_name):
        """Mengecek ketersediaan nama paket di registry publik"""
        url = self.registries[ecosystem].format(package_name)
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 404:
                return False # Paket TIDAK ADA di publik (Bisa dibajak!)
            return True # Paket ada (Aman/Sudah terdaftar)
        except:
            return True # Asumsikan aman jika error koneksi

    def audit_npm(self):
        """Mencari dan mengaudit package.json"""
        print(f"\n{Fore.WHITE}   >>> Checking NPM (Node.js) Configuration...{Style.RESET_ALL}")
        url = f"{self.target}/package.json"
        
        try:
            res = self.session.get(url, timeout=5)
            if res.status_code == 200 and "dependencies" in res.text:
                print(f"   {Fore.RED}[EXPOSED] package.json found! Parsing dependencies...{Style.RESET_ALL}")
                try:
                    data = res.json()
                    deps = data.get('dependencies', {})
                    dev_deps = data.get('devDependencies', {})
                    all_deps = {**deps, **dev_deps}
                    
                    for pkg, ver in all_deps.items():
                        # Skip paket scoped (@angular/core) biasanya aman atau private registry
                        if pkg.startswith("@"): continue 
                        
                        exists_public = self.check_registry('NPM', pkg)
                        if not exists_public:
                            print(f"      {Fore.RED}[CRITICAL] Dependency Confusion Risk: '{pkg}'{Style.RESET_ALL}")
                            print(f"      └── Status: Not found on NPM Public Registry. Attacker can claim this name!")
                        else:
                            print(f"      {Fore.GREEN}[SAFE] {pkg} exists on public registry.{Style.RESET_ALL}")
                except:
                    print(f"      [!] Failed to parse JSON.")
            else:
                print(f"   {Fore.GREEN}[SAFE] package.json not exposed.{Style.RESET_ALL}")
        except:
            pass

    def audit_composer(self):
        """Mencari dan mengaudit composer.json"""
        print(f"\n{Fore.WHITE}   >>> Checking Composer (PHP) Configuration...{Style.RESET_ALL}")
        url = f"{self.target}/composer.json"
        
        try:
            res = self.session.get(url, timeout=5)
            if res.status_code == 200 and "require" in res.text:
                print(f"   {Fore.RED}[EXPOSED] composer.json found! Parsing...{Style.RESET_ALL}")
                try:
                    data = res.json()
                    reqs = data.get('require', {})
                    
                    for pkg, ver in reqs.items():
                        if "/" not in pkg: continue # Format composer vendor/package
                        
                        exists_public = self.check_registry('Composer', pkg)
                        if not exists_public:
                            print(f"      {Fore.RED}[CRITICAL] Dependency Confusion Risk: '{pkg}'{Style.RESET_ALL}")
                            print(f"      └── Status: Not found on Packagist. Hijacking possible!")
                except:
                    pass
            else:
                print(f"   {Fore.GREEN}[SAFE] composer.json not exposed.{Style.RESET_ALL}")
        except:
            pass

    def audit_wordpress_plugins(self):
        """Mengecek Plugin WordPress yang sudah dihapus dari Repo (Abandoned/Vuln)"""
        print(f"\n{Fore.WHITE}   >>> Checking WordPress Plugin Supply Chain...{Style.RESET_ALL}")
        # Teknik pasif: kita coba tebak plugin umum atau baca dari source code (simulasi)
        # Di sini kita coba akses readme plugin umum untuk demo
        common_plugins = ["contact-form-7", "yoast-seo", "elementor", "jetpack", "wp-super-cache"]
        
        for plugin in common_plugins:
            readme_url = f"{self.target}/wp-content/plugins/{plugin}/readme.txt"
            try:
                res = self.session.get(readme_url, timeout=3)
                if res.status_code == 200:
                    # Cek apakah masih ada di WP Repo
                    repo_url = self.registries['WordPress'].format(plugin)
                    repo_res = requests.get(repo_url, timeout=5)
                    
                    if repo_res.status_code == 404:
                        print(f"   {Fore.RED}[CRITICAL] Abandoned Plugin Detected: '{plugin}'{Style.RESET_ALL}")
                        print(f"   └── Installed on target but REMOVED from WordPress Repository (Likely Vulnerable/Malware).")
                    else:
                        print(f"   {Fore.GREEN}[SAFE] Plugin '{plugin}' is active on repo.{Style.RESET_ALL}")
            except:
                pass

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Supply Chain & Dependency Auditor{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[*] Focus: Finding exposed config files & internal package names.")
        
        self.audit_npm()
        self.audit_composer()
        self.audit_wordpress_plugins()
        
        print("-" * 60)
        print(f"{Fore.CYAN}[*] Audit Completed.{Style.RESET_ALL}")

def run_supply_scan(url):
    engine = SupplyChainAuditor(url)
    engine.run_scan()