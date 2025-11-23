import requests
from colorama import Fore, Style

def run_robots_check(url):
    print(f"\n{Fore.CYAN}[*] MODULE START: Hidden Path Scanner (Robots.txt){Style.RESET_ALL}")
    
    # Pastikan format URL benar (harus base url)
    if not url.endswith('/'):
        url += '/'
    
    target_url = url + "robots.txt"
    print(f"{Fore.WHITE}[*] Fetching: {Fore.GREEN}{target_url}")
    print("-" * 60)

    try:
        headers = {'User-Agent': 'ZeroBurst-Scanner/4.0'}
        response = requests.get(target_url, headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"{Fore.GREEN}[SUCCESS] Robots.txt Found!{Style.RESET_ALL}")
            print(f"{Fore.WHITE}[*] Interesting Entries Detected:\n")
            
            lines = response.text.splitlines()
            found_something = False
            
            for line in lines:
                # Kita cari baris 'Disallow' karena itu folder yang disembunyikan
                if "Disallow:" in line:
                    path = line.split(":")[1].strip()
                    if path and path != "/":
                        print(f"   {Fore.RED}[RESTRICTED] {path} {Style.RESET_ALL}")
                        found_something = True
            
            if not found_something:
                print(f"   {Fore.YELLOW}[INFO] File ditemukan, tapi tidak ada path rahasia.")
        else:
            print(f"{Fore.RED}[404] Robots.txt not found on this server.")

    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}")

    print("-" * 60)