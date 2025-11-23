import requests
from colorama import Fore, Style

def run_header_check(url):
    print(f"\n{Fore.CYAN}[*] MODULE START: HTTP Header Analysis{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Target URL: {Fore.GREEN}{url}")
    print("-" * 50)

    try:
        # User-Agent agar tidak diblokir firewall sederhana
        user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=user_agent, timeout=10)
        
        headers = response.headers
        
        # List header keamanan penting
        security_headers = [
            "X-Frame-Options",
            "X-XSS-Protection",
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "Referrer-Policy"
        ]

        print(f"Status Code: {Fore.YELLOW}{response.status_code}{Style.RESET_ALL}")
        print(f"Server Info: {Fore.MAGENTA}{headers.get('Server', 'Hidden')}{Style.RESET_ALL}\n")

        print(f"{Fore.WHITE}[ Checking Security Headers ]")
        for check in security_headers:
            if check in headers:
                print(f"{Fore.GREEN}[OK] {check} detected.")
            else:
                print(f"{Fore.RED}[MISSING] {check} not found!")

    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}[!] Connection Error: {e}")
    
    print("-" * 50)