import requests
import concurrent.futures
from colorama import Fore, Style

class SecretHunter:
    def __init__(self, target_url):
        self.target = target_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-SecretHunter/29.0'}
        
        # WORDLIST: File Paling Berbahaya & Sering Bocor
        self.sensitive_files = [
            # Configs & Secrets
            ".env", ".env.example", ".env.bak", ".env.production",
            "config.php.bak", "config.php.old", "config.php.save",
            "web.config", "phpinfo.php", "info.php",
            "conf/server.xml", "database.yml", "settings.py",
            
            # Version Control
            ".git/config", ".git/HEAD", ".svn/entries", ".DS_Store",
            ".gitlab-ci.yml", ".travis.yml",
            
            # Backups
            "backup.sql", "database.sql", "dump.sql", "users.sql",
            "backup.zip", "site.tar.gz", "www.rar", "bkp.zip",
            
            # Keys
            "id_rsa", "id_rsa.pub", "server.key", "private.key",
            
            # Logs
            "error_log", "access_log", "debug.log", "storage/logs/laravel.log",
            
            # Admin Panels (Common)
            "admin.php", "administrator/", "login.php", "wp-login.php",
            "dashboard/", "panel/", "cpanel/"
        ]
        
        self.found_secrets = []

    def check_file(self, filename):
        """Mengecek apakah file ada (200 OK)"""
        url = f"{self.target}/{filename}"
        try:
            res = self.session.get(url, timeout=5, allow_redirects=False)
            
            # Filter 200 OK Only
            if res.status_code == 200:
                # Verifikasi Konten (False Positive Check)
                # Misal: .env harus ada "DB_" atau "APP_"
                content = res.text.lower()
                confidence = "Medium"
                
                if filename == ".env" and "db_" in content: confidence = "CRITICAL"
                elif ".git" in filename and "repository" in content: confidence = "CRITICAL"
                elif ".sql" in filename and "create table" in content: confidence = "CRITICAL"
                elif "phpinfo" in filename and "php version" in content: confidence = "High"
                
                # Ignore Soft 404 (Halaman error custom yang return 200)
                if "page not found" in content or len(content) < 10:
                    return

                print(f"   {Fore.GREEN}[FOUND] {url:<50} | Status: 200 | Risk: {confidence}{Style.RESET_ALL}")
                self.found_secrets.append((url, confidence))
                
            elif res.status_code == 403:
                print(f"   {Fore.YELLOW}[FORBIDDEN] {url:<50} | Status: 403 (Exists but Locked){Style.RESET_ALL}")

        except:
            pass

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Sensitive File & Backup Hunter{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[*] Mode: High-Value Target Brute Force")
        print("-" * 80)

        # Multi-Threading Cepat (30 Workers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            executor.map(self.check_file, self.sensitive_files)

        print("-" * 80)
        if self.found_secrets:
            print(f"{Fore.RED}[!!!] SCAN COMPLETE: Found {len(self.found_secrets)} sensitive files exposed!{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Impact: Database Credential Leak, Source Code Theft.")
        else:
            print(f"{Fore.GREEN}[OK] No common sensitive files found publicly.{Style.RESET_ALL}")

def run_secret_scan(url):
    engine = SecretHunter(url)
    engine.run_scan()