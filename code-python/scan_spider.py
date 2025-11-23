import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from colorama import Fore, Style
import time

def run_spider(target_url, return_mode=False):
    if not return_mode:
        print(f"\n{Fore.CYAN}[*] MODULE START: Automated Spider{Style.RESET_ALL}")
    
    # Pastikan format URL benar
    if not target_url.startswith('http'):
        target_url = 'http://' + target_url

    base_domain = urlparse(target_url).netloc
    visited_urls = set()
    urls_to_visit = [target_url]
    
    # List untuk menyimpan URL "matang" (yang punya parameter)
    vulnerable_candidates = [] 

    headers = {'User-Agent': 'ZeroBurst-AutoScanner/5.5'}
    
    # Batasan halaman agar tidak kelamaan
    max_pages = 25 
    count = 0

    print(f"{Fore.WHITE}[*] Crawling & Harvesting Parameters from: {Fore.GREEN}{base_domain}")
    
    try:
        while urls_to_visit and count < max_pages:
            current_url = urls_to_visit.pop(0)
            if current_url in visited_urls: continue

            try:
                # Request cepat
                response = requests.get(current_url, headers=headers, timeout=3)
                visited_urls.add(current_url)
                count += 1
                
                # Tampilkan proses scan kecil saja
                print(f"\r{Fore.YELLOW}[Spider] {Fore.WHITE}Scanning Page {count}/{max_pages}: {current_url[:40]}...", end="")

                if response.status_code != 200: continue

                soup = BeautifulSoup(response.text, 'html.parser')

                for link in soup.find_all('a'):
                    href = link.get('href')
                    if not href: continue
                    
                    full_url = urljoin(current_url, href)
                    if urlparse(full_url).netloc == base_domain:
                        if full_url not in visited_urls and full_url not in urls_to_visit:
                            if not full_url.endswith(('.png', '.jpg', '.css', '.js')):
                                urls_to_visit.append(full_url)
                        
                        # INI LOGIKA PENTINGNYA:
                        # Jika ada tanda tanya (?) dan sama dengan (=), simpan!
                        if "?" in full_url and "=" in full_url:
                            if full_url not in vulnerable_candidates:
                                vulnerable_candidates.append(full_url)
                                # Tampilkan tanda bahwa URL target ditemukan
                                print(f"\n   {Fore.GREEN}[+] TARGET ACQUIRED: {full_url}")

            except:
                pass
            
    except KeyboardInterrupt:
        print("\n[!] Spider stopped.")

    print(f"\n{Fore.CYAN}[*] Spider selesai. Ditemukan {len(vulnerable_candidates)} URL potensial.")
    
    # KEMBALIKAN DATA KE MENU UTAMA
    return vulnerable_candidates