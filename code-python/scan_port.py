import socket
import concurrent.futures
import re
import requests
from colorama import Fore, Style

class AdvancedPortScanner:
    def __init__(self, target_host):
        self.target = target_host
        # Resolving Hostname to IP
        try:
            self.ip = socket.gethostbyname(target_host)
        except:
            self.ip = None
            
        # Top 100 Common Ports (Untuk kecepatan)
        self.common_ports = [
            21, 22, 23, 25, 53, 80, 81, 110, 111, 135, 139, 143, 443, 445, 993, 995,
            1723, 3306, 3389, 5900, 8000, 8080, 8081, 8443, 8888, 9000, 27017, 6379,
            11211, 5432, 1521, 2082, 2083, 2086, 2087, 5000, 1433
        ]
        
        # DATABASE CVE SEDERHANA (Simulasi Vulnerability Mapping)
        # Format: "Nama Service & Versi": "CVE-XXXX-YYYY (Nama Celah)"
        self.cve_database = {
            "vsFTPd 2.3.4": "CVE-2011-2523 (Backdoor Command Execution)",
            "Apache 2.4.49": "CVE-2021-41773 (Path Traversal & RCE)",
            "Apache 2.4.50": "CVE-2021-42013 (Path Traversal & RCE)",
            "OpenSSH 7.2p2": "CVE-2016-6210 (User Enumeration)",
            "OpenSSL 1.0.1": "CVE-2014-0160 (Heartbleed)",
            "ProFTPD 1.3.5": "CVE-2015-3306 (Mod_Copy RCE)",
            "Samba 3.0.20": "CVE-2007-2447 (Username Map Script RCE)",
            "WebLogic": "CVE-2020-14882 (RCE)",
            "Struts 2": "CVE-2017-5638 (RCE)",
            "Elasticsearch 1.4": "CVE-2015-1427 (RCE Scripting)"
        }

    def grab_banner(self, port, sock):
        """Mencoba mengambil banner/versi dari service"""
        try:
            # Untuk HTTP, kita harus kirim request dulu
            if port in [80, 8080, 443, 8443]:
                sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
            
            # Terima respon
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            return banner
        except:
            return "Unknown Service"

    def check_port(self, port):
        """Worker function untuk scanning satu port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.5) # Timeout cepat
            result = sock.connect_ex((self.ip, port))
            
            if result == 0:
                # Port Terbuka! Ambil Banner
                banner = self.grab_banner(port, sock)
                sock.close()
                
                # Bersihkan banner (hanya ambil baris pertama yang relevan)
                clean_banner = banner.split('\n')[0][:50] 
                
                # Deteksi Service
                service = "Unknown"
                try:
                    service = socket.getservbyport(port)
                except:
                    pass

                return (port, service, clean_banner)
            sock.close()
        except:
            pass
        return None

    def analyze_cve(self, banner):
        """Mencocokkan Banner dengan Database CVE"""
        vulns = []
        for software, cve in self.cve_database.items():
            if software.lower() in banner.lower():
                vulns.append(cve)
        return vulns

    def run_port_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Advanced Port & Service Scanning{Style.RESET_ALL}")
        
        if not self.ip:
            print(f"{Fore.RED}[!] Could not resolve hostname.{Style.RESET_ALL}")
            return

        print(f"{Fore.WHITE}[*] Target IP: {Fore.GREEN}{self.ip}")
        print(f"{Fore.WHITE}[*] Scanning Top {len(self.common_ports)} Ports with Service Detection...")
        print("-" * 80)
        print(f"   {'PORT':<10} | {'SERVICE':<15} | {'BANNER / VERSION':<30} | {'CVE ANALYSIS'}")
        print("-" * 80)

        open_ports = 0
        
        # Multi-Threading Scan
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(self.check_port, self.common_ports)
            
            for res in results:
                if res:
                    port, service, banner = res
                    open_ports += 1
                    
                    # Analisis CVE
                    cve_hits = self.analyze_cve(banner)
                    cve_text = ""
                    if cve_hits:
                        cve_text = f"{Fore.RED}{cve_hits[0]}{Style.RESET_ALL}"
                    else:
                        cve_text = f"{Fore.GREEN}Clean{Style.RESET_ALL}"

                    # Formatting Output
                    if not banner: banner = "No Banner"
                    
                    print(f"   {port:<10} | {service:<15} | {Fore.YELLOW}{banner:<30}{Style.RESET_ALL} | {cve_text}")

        print("-" * 80)
        print(f"{Fore.GREEN}[*] Scan Completed. Found {open_ports} open ports.{Style.RESET_ALL}")

def run_port_scan(host):
    scanner = AdvancedPortScanner(host)
    scanner.run_port_scan()