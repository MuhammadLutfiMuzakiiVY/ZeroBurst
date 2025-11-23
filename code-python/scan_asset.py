import requests
import dns.resolver
import concurrent.futures
import socket
from colorama import Fore, Style

class AssetHunter:
    def __init__(self, target_domain):
        # Bersihkan input (hanya domain utama)
        self.domain = target_domain.replace("http://", "").replace("https://", "").split("/")[0]
        if ":" in self.domain: self.domain = self.domain.split(":")[0]
        
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 2
        self.resolver.lifetime = 2
        
        # DATABASE SIGNATURE CDN/CLOUD
        self.cdn_fingerprints = {
            'Cloudflare': ['cloudflare', 'cdn.cloudflare.net'],
            'AWS CloudFront': ['cloudfront.net'],
            'AWS S3': ['s3.amazonaws.com'],
            'Akamai': ['akamai', 'akadns', 'edgekey'],
            'Fastly': ['fastly', 'fastlylb'],
            'Azure': ['azure', 'azurewebsites', 'trafficmanager'],
            'Google Cloud': ['googlehosted', 'appspot'],
            'Heroku': ['herokuapp'],
            'Github Pages': ['github.io'],
            'DigitalOcean': ['digitaloceanspaces']
        }
        
        # Wordlist Subdomain (Top 150 Common)
        self.subdomains = [
            "www", "mail", "remote", "blog", "webmail", "server", "ns1", "ns2", "smtp", "secure",
            "vpn", "m", "shop", "ftp", "mail2", "test", "portal", "ns", "ww1", "host", "support",
            "dev", "web", "bbs", "ww42", "mx", "email", "cloud", "1", "mail1", "2", "forum",
            "admin", "www1", "news", "app", "cdn", "public", "static", "beta", "api", "staging",
            "files", "media", "mobile", "store", "dashboard", "auth", "login", "jenkins", "gitlab",
            "git", "jira", "confluence", "monitor", "zabbix", "grafana", "kibana", "prometheus",
            "payment", "checkout", "account", "member", "billing", "finance", "marketing", "sales",
            "internal", "intranet", "corp", "employee", "hr", "career", "jobs", "docs", "wiki",
            "help", "status", "uptime", "gateway", "proxy", "node", "cluster", "db", "sql", "mysql",
            "oracle", "postgres", "redis", "mongo", "elasticsearch", "search", "images", "img", "video",
            "assets", "download", "upload", "ftp1", "ftp2", "sftp", "ssh", "telnet", "iot", "camera",
            "office", "outlook", "exchange", "owa", "autodiscover", "autoconfig", "cpanel", "whm",
            "plesk", "directadmin", "webdisk", "cp", "control", "manage", "manager", "sys", "system",
            "root", "base", "core", "v1", "v2", "api-v1", "api-v2", "graphql", "rest", "soap"
        ]
        
        self.found_assets = []

    def identify_cdn(self, cname_value):
        """Mencocokkan CNAME dengan database CDN"""
        cname = str(cname_value).lower()
        for provider, sigs in self.cdn_fingerprints.items():
            for sig in sigs:
                if sig in cname:
                    return f"{Fore.MAGENTA}[{provider}]{Style.RESET_ALL}"
        return f"{Fore.WHITE}[Direct/Unknown]{Style.RESET_ALL}"

    def check_asset(self, sub):
        """Cek DNS dan status hidup"""
        full_domain = f"{sub}.{self.domain}"
        
        try:
            # 1. Cek A Record (IP)
            a_records = self.resolver.resolve(full_domain, 'A')
            ip = a_records[0].to_text()
            
            # 2. Cek CNAME (Untuk deteksi Cloud/CDN)
            cname_info = "Direct IP"
            cdn_tag = ""
            try:
                cname_records = self.resolver.resolve(full_domain, 'CNAME')
                cname_target = cname_records[0].target.to_text()
                cname_info = f"-> {cname_target}"
                cdn_tag = self.identify_cdn(cname_target)
            except:
                pass # Tidak ada CNAME

            # 3. Cek HTTP Status (Asset Alive?)
            status_code = "---"
            try:
                res = requests.get(f"http://{full_domain}", timeout=3)
                status_code = str(res.status_code)
                if "200" in status_code: status_code = f"{Fore.GREEN}200 OK{Style.RESET_ALL}"
                elif "403" in status_code: status_code = f"{Fore.YELLOW}403 Forbidden{Style.RESET_ALL}"
                elif "404" in status_code: status_code = f"{Fore.RED}404 Not Found{Style.RESET_ALL}"
                elif "30" in status_code: status_code = f"{Fore.CYAN}Redirect{Style.RESET_ALL}"
            except:
                status_code = f"{Fore.RED}Down/Timeout{Style.RESET_ALL}"

            # Print Hasil
            print(f"   {Fore.GREEN}[+] FOUND:{Style.RESET_ALL} {full_domain:<30} | {ip:<15} | {status_code:<15} {cdn_tag}")
            
            self.found_assets.append({
                'domain': full_domain,
                'ip': ip,
                'cname': cname_info
            })

        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            pass
        except Exception:
            pass

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Asset & Cloud Discovery (Subdomain Hunter){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target Scope: {Fore.GREEN}{self.domain}")
        print(f"{Fore.WHITE}[*] Wordlist Size: {len(self.subdomains)} common names")
        print("-" * 80)
        print(f"   {'SUBDOMAIN':<30} | {'IP ADDRESS':<15} | {'HTTP STATUS':<15} | {'CLOUD/CDN'}")
        print("-" * 80)

        # Multi-Threading 25 Workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            executor.map(self.check_asset, self.subdomains)

        print("-" * 80)
        print(f"{Fore.GREEN}[*] Asset Discovery Completed. Found {len(self.found_assets)} exposed assets.{Style.RESET_ALL}")

def run_asset_scan(url):
    engine = AssetHunter(url)
    engine.run_scan()