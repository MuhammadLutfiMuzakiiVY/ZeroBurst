import requests
import os
from colorama import Fore, Style

class UploadScanner:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-UploadAuditor/49.0'}
        
        # Ekstensi yang berisiko jika diterima server
        self.risky_extensions = [
            ".php", ".php5", ".phtml", ".exe", ".sh", ".jsp", 
            ".asp", ".aspx", ".cgi", ".pl", ".html", ".svg"
        ]
        
        # Dummy content untuk testing (Safe Payload)
        self.dummy_content = b"ZeroBurst Security Audit Test File"

    def audit_upload_endpoint(self, upload_url, input_name):
        """
        Menguji validasi upload dengan mengirim file 'aman' 
        namun dengan ekstensi yang seharusnya diblokir.
        """
        print(f"\n{Fore.YELLOW}[+] Auditing Upload Logic on: {input_name}...{Style.RESET_ALL}")
        
        for ext in self.risky_extensions:
            filename = f"test_zeroburst{ext}"
            files = {
                input_name: (filename, self.dummy_content, 'application/octet-stream')
            }
            
            try:
                # Kirim Request Upload
                res = self.session.post(upload_url, files=files, timeout=10)
                
                # Analisis Respon
                # Indikator keberhasilan upload seringkali status 200/201 atau ada kata 'success'
                if res.status_code in [200, 201] and "success" in res.text.lower():
                    print(f"   {Fore.RED}[WARNING] Server accepted risky extension: {ext}{Style.RESET_ALL}")
                    print(f"   └── Status: {res.status_code} | Response might indicate success.")
                elif res.status_code == 403 or "denied" in res.text.lower() or "not allowed" in res.text.lower():
                    print(f"   {Fore.GREEN}[SAFE] Extension {ext} blocked.{Style.RESET_ALL}")
                else:
                    # print(f"   [INFO] {ext} returned status {res.status_code}")
                    pass
                    
            except Exception as e:
                pass

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Insecure File Upload Auditor{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        # Modul ini membutuhkan URL spesifik tempat form upload berada (biasanya POST)
        # Jika user memberikan URL GET biasa, kita coba cari form upload dulu (integrasi mini-crawler)
        
        try:
            from bs4 import BeautifulSoup
            res = self.session.get(self.target, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            forms = soup.find_all('form')
            
            found_upload = False
            for form in forms:
                # Cari input type file
                file_input = form.find('input', {'type': 'file'})
                if file_input:
                    found_upload = True
                    action = form.get('action') or self.target
                    if not action.startswith('http'):
                        import urllib.parse
                        action = urllib.parse.urljoin(self.target, action)
                    
                    input_name = file_input.get('name')
                    print(f"\n{Fore.MAGENTA}[FOUND] Upload Form Detected!{Style.RESET_ALL}")
                    print(f"   ├── Action: {action}")
                    print(f"   └── Input : {input_name}")
                    
                    if input_name:
                        self.audit_upload_endpoint(action, input_name)
            
            if not found_upload:
                print(f"{Fore.RED}[-] No file upload forms detected on this page.{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")

def run_upload_scan(url):
    engine = UploadScanner(url)
    engine.run_scan()