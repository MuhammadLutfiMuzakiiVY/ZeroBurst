import requests
import concurrent.futures
from colorama import Fore, Style

class AdminPanelHunter:
    def __init__(self, target_url):
        self.target = target_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-AdminHunter/50.0'}
        
        # Wordlist Jalur Admin Umum (Top Used)
        self.admin_paths = [
            "admin", "administrator", "admin_panel", "controlpanel", "login",
            "wp-admin", "wp-login.php", "admin.php", "cp", "manage", 
            "manager", "management", "administration", "panel", "dashboard",
            "auth", "user", "member", "account", "signin", "backend",
            "siteadmin", "myadmin", "webadmin", "admins", "root",
            "system", "admin/login", "admin/home", "moderator", "cms",
            "joomla/administrator", "typo3", "bitrix", "drupal",
            "cpanel", "whm", "plesk", "webmin", "kloxo"
        ]

    def check_path(self, path):
        """Mengecek status kode HTTP dari path"""
        url = f"{self.target}/{path}"
        try:
            # Allow redirects=True untuk melihat apakah dilempar ke halaman login
            res = self.session.get(url, timeout=5, allow_redirects=False)
            
            status = res.status_code
            size = len(res.text)
            
            # Analisis Temuan
            if status == 200:
                # Saring halaman kosong/parkir
                if "login" in res.text.lower() or "password" in res.text.lower() or "admin" in res.text.lower():
                    print(f"   {Fore.RED}[EXPOSED] {url:<50} | Status: 200 (Login Page Detected){Style.RESET_ALL}")
                    return True
                elif size > 500:
                    print(f"   {Fore.YELLOW}[FOUND]   {url:<50} | Status: 200 | Size: {size}{Style.RESET_ALL}")
                    return True
            
            elif status in [301, 302, 307, 308]:
                # Redirect seringkali mengarah ke halaman login yang sebenarnya
                location = res.headers.get('Location', 'Unknown')
                print(f"   {Fore.CYAN}[REDIRECT] {url:<50} -> {location}{Style.RESET_ALL}")
                return True
                
            elif status == 401:
                print(f"   {Fore.MAGENTA}[AUTH]    {url:<50} | Status: 401 (Basic Auth Required){Style.RESET_ALL}")
                return True
                
            elif status == 403:
                # 403 berarti ada, tapi diblokir (Good sign for admin panel existence)
                print(f"   {Fore.BLUE}[LOCKED]   {url:<50} | Status: 403 (Forbidden){Style.RESET_ALL}")
                return True

        except:
            pass
        return False

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Admin Panel Exposure Hunter{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[*] Wordlist: {len(self.admin_paths)} common paths")
        print("-" * 80)

        found_panels = 0
        
        # Multi-Threading 20 Workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(self.check_path, self.admin_paths)
            for r in results:
                if r: found_panels += 1

        print("-" * 80)
        if found_panels > 0:
            print(f"{Fore.RED}[!!!] SCAN COMPLETE: {found_panels} Potential Admin Panels Found.{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Recommendation: Restrict access via IP Whitelist or move to non-standard path.")
        else:
            print(f"{Fore.GREEN}[OK] No standard admin panels exposed publicly.{Style.RESET_ALL}")

def run_admin_scan(url):
    engine = AdminPanelHunter(url)
    engine.run_scan()