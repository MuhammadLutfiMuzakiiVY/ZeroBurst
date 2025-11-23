import requests
import socket
import dns.resolver
from colorama import Fore, Style

def check_cloud_buckets(domain):
    print(f"\n{Fore.CYAN}[*] MODULE START: Cloud Storage & CDN Auditor{Style.RESET_ALL}")
    
    # 1. S3 BUCKET GUESSING
    clean_domain = domain.replace("http://", "").replace("https://", "").split("/")[0]
    base_name = clean_domain.split(".")[0]
    
    buckets = [
        f"http://{base_name}.s3.amazonaws.com",
        f"http://{base_name}-assets.s3.amazonaws.com",
        f"http://{base_name}-dev.s3.amazonaws.com",
        f"https://storage.googleapis.com/{base_name}",
        f"https://{base_name}.blob.core.windows.net/public"
    ]
    
    print(f"{Fore.YELLOW}[+] Checking for Public Cloud Buckets...{Style.RESET_ALL}")
    for bucket in buckets:
        try:
            res = requests.get(bucket, timeout=3)
            if res.status_code == 200 and ("ListBucketResult" in res.text or "xml" in res.text):
                print(f"   {Fore.RED}[CRITICAL] OPEN BUCKET FOUND: {bucket}{Style.RESET_ALL}")
                print(f"   └── Content listing enabled (Data Leak).")
            elif res.status_code == 403:
                print(f"   {Fore.YELLOW}[FOUND] Protected Bucket: {bucket} (Exists but locked){Style.RESET_ALL}")
        except:
            pass

    # 2. CDN BYPASS (ORIGIN IP SCAN)
    # Mencoba mencari IP asli di balik Cloudflare via DNS History (Simulasi)
    print(f"\n{Fore.YELLOW}[+] Checking CDN/WAF Bypass Potential...{Style.RESET_ALL}")
    try:
        # Cek subdomain umum yang sering lupa diproteksi CDN
        direct_subs = ["direct", "origin", "ftp", "cpanel", "mail"]
        for sub in direct_subs:
            target = f"{sub}.{clean_domain}"
            try:
                ip = socket.gethostbyname(target)
                print(f"   {Fore.CYAN}[INFO] Potential Origin: {target} -> {ip}{Style.RESET_ALL}")
            except:
                pass
    except:
        pass
    print("-" * 60)