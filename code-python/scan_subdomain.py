import requests
import dns.resolver
import concurrent.futures
from colorama import Fore, Style

class SubdomainHunter:
    def __init__(self, target_domain):
        # Membersihkan input agar hanya sisa domain (misal: google.com)
        self.domain = target_domain.replace("http://", "").replace("https://", "").split("/")[0]
        if ":" in self.domain:
            self.domain = self.domain.split(":")[0]
            
        # WORDLIST: Daftar nama subdomain umum (Top 100 Common)
        self.subdomains = [
            "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "webdisk", "ns2",
            "cpanel", "whm", "autodiscover", "autoconfig", "m", "imap", "test", "ns", "blog", "pop3",
            "dev", "www2", "admin", "forum", "ispsystem", "ns3", "mail2", "server", "ns4", "directory",
            "search", "shop", "api", "support", "secure", "vpn", "jenkins", "gitlab", "git", "status",
            "portal", "beta", "staging", "auth", "login", "payment", "checkout", "account", "dashboard",
            "monitor", "gateway", "service", "files", "download", "upload", "cdn", "static", "assets",
            "internal", "intranet", "demo", "public", "store", "media", "images", "img", "video",
            "kb", "help", "wiki", "docs", "jira", "confluence", "slack", "grafana", "prometheus", "kibana",
            "sftp", "ssh", "telnet", "remote", "db", "database", "mysql", "sql", "redis", "mongodb",
            "oracle", "postgres", "aws", "s3", "azure", "cloud", "backup", "old", "new", "temp"
        ]
        
        self.found_subdomains = []

    def check_subdomain(self, sub):
        """Mengecek apakah subdomain aktif via DNS Resolution"""
        full_sub = f"{sub}.{self.domain}"
        try:
            # Cek DNS (Lebih cepat daripada HTTP Request)
            answers = dns.resolver.resolve(full_sub, 'A')
            ip_address = answers[0].to_text()
            
            # Jika resolve sukses, kita print
            print(f"   {Fore.GREEN}[+] FOUND: {Fore.WHITE}{full_sub:<30} {Fore.CYAN}-> {ip_address}{Style.RESET_ALL}")
            self.found_subdomains.append((full_sub, ip_address))
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            # Tidak ditemukan
            pass
        except Exception:
            pass

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Subdomain Discovery Hunter (Multi-Threaded){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target Domain: {Fore.GREEN}{self.domain}")
        print(f"{Fore.WHITE}[*] Wordlist Size: {len(self.subdomains)} common names")
        print("-" * 60)

        # Menggunakan ThreadPoolExecutor untuk kecepatan tinggi (Scanning paralel)
        # Scan 20 subdomain sekaligus
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(self.check_subdomain, self.subdomains)

        print("-" * 60)
        if self.found_subdomains:
            print(f"{Fore.GREEN}[SUCCESS] Total Subdomains Found: {len(self.found_subdomains)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[TIP] Coba scan target subdomain tersebut untuk mencari celah spesifik!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[!] No common subdomains found. Try using external wordlist.{Style.RESET_ALL}")

def run_subdomain_scan(url):
    engine = SubdomainHunter(url)
    engine.run_scan()