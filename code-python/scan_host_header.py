import requests
from colorama import Fore, Style

def run_host_header_scan(url):
    print(f"\n{Fore.CYAN}[*] MODULE START: Host Header Injection Auditor{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{url}")
    
    headers = {
        'Host': 'evil.com',
        'X-Forwarded-Host': 'evil.com'
    }
    
    try:
        # Request dengan Host palsu
        res = requests.get(url, headers=headers, timeout=5, allow_redirects=False)
        
        is_vuln = False
        proof = ""
        
        # Cek apakah 'evil.com' terpantul di Location Header (Redirect)
        if 'Location' in res.headers and 'evil.com' in res.headers['Location']:
            is_vuln = True
            proof = f"Location Header: {res.headers['Location']}"
            
        # Cek apakah terpantul di Body (misal di link script/css)
        elif 'evil.com' in res.text:
            is_vuln = True
            proof = "Reflected in Response Body (Check links/scripts)"
            
        if is_vuln:
            print(f"   {Fore.RED}[CRITICAL] HOST HEADER INJECTION DETECTED!{Style.RESET_ALL}")
            print(f"   └── Proof: {proof}")
            print(f"   └── Risk : Password Reset Poisoning, Cache Poisoning.")
        else:
            print(f"   {Fore.GREEN}[SAFE] Server ignored fake Host header.{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}")
    print("-" * 60)