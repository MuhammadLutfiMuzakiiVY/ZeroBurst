import requests
import socket
from colorama import Fore, Style

def run_geo_ip(host):
    print(f"\n{Fore.CYAN}[*] MODULE START: Geo-Location Tracker{Style.RESET_ALL}")
    
    try:
        # Ubah domain jadi IP dulu
        target_ip = socket.gethostbyname(host)
        print(f"{Fore.WHITE}[*] Resolving Host: {Fore.GREEN}{host} -> {target_ip}")
        print("-" * 50)
        
        # Request ke API
        url_api = f"http://ip-api.com/json/{target_ip}"
        response = requests.get(url_api, timeout=10)
        data = response.json()
        
        if data['status'] == 'success':
            print(f"   {Fore.YELLOW}[INFO FOUND]{Style.RESET_ALL}")
            print(f"   Country     : {data.get('country')}")
            print(f"   Region/City : {data.get('regionName')} - {data.get('city')}")
            print(f"   ISP Name    : {data.get('isp')}")
            print(f"   Timezone    : {data.get('timezone')}")
            print(f"   Coordinates : {data.get('lat')}, {data.get('lon')}")
        else:
            print(f"{Fore.RED}[!] Failed to track location (Private IP?).")

    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}")

    print("-" * 50)