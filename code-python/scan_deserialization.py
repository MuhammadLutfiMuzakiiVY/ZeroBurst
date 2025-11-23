import requests
import re
import base64
import binascii
from colorama import Fore, Style

class DeserializationHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-DeserializationHunter/43.0'}

    def is_base64(self, s):
        """Cek apakah string adalah Base64 valid"""
        try:
            if len(s) % 4 == 0:
                base64.b64decode(s, validate=True)
                return True
        except:
            pass
        return False

    def analyze_data(self, data_str, location):
        """Menganalisis string untuk mencari signature serialisasi"""
        if not data_str: return

        # 1. JAVA SERIALIZATION (Hex: AC ED 00 05)
        # Seringkali dikirim dalam bentuk Base64 (rO0AB...)
        if "rO0AB" in data_str:
            print(f"   {Fore.RED}[CRITICAL] Java Serialized Object Detected!{Style.RESET_ALL}")
            print(f"   ├── Location : {location}")
            print(f"   └── Signature: Base64 starts with 'rO0AB' (Magic Bytes AC ED 00 05)")
            print(f"   └── Risk     : Remote Code Execution (RCE) via Gadget Chain (e.g. CommonsCollections)")

        # 2. PHP SERIALIZATION
        # Format: O:4:"User":2:{...} atau a:2:{...}
        # Regex: O:\d+:"[a-zA-Z0-9_]+":\d+:
        if re.search(r'[Oa]:\d+:["]?[a-zA-Z0-9_]+["]?:', data_str):
            print(f"   {Fore.RED}[CRITICAL] PHP Serialized Data Detected!{Style.RESET_ALL}")
            print(f"   ├── Location : {location}")
            print(f"   └── Pattern  : Matches PHP Object Injection signature")
            print(f"   └── Risk     : RCE via __wakeup() or __destruct()")

        # 3. PYTHON PICKLE
        # Seringkali diawali byte tertentu, tapi di web biasanya Base64.
        # Indikator lemah: cos\nsystem\n(S'...'
        if "gASV" in data_str or "c__builtin__" in data_str: # gASV adalah header umum pickle base64
            print(f"   {Fore.RED}[CRITICAL] Python Pickle Data Detected!{Style.RESET_ALL}")
            print(f"   ├── Location : {location}")
            print(f"   └── Risk     : Arbitrary Code Execution (Pickle is insecure by design)")

        # 4. ASP.NET VIEWSTATE
        if "__VIEWSTATE" in location or (len(data_str) > 20 and data_str.startswith("/wEP")):
            print(f"   {Fore.YELLOW}[INFO] ASP.NET ViewState Detected{Style.RESET_ALL}")
            print(f"   ├── Location : {location}")
            # Cek apakah terenkripsi (Heuristic simple)
            # Tools lain seperti ViewStateDecoder lebih akurat untuk ini
            print(f"   └── Note     : Check if MAC validation/Encryption is enabled.")

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Insecure Deserialization Detector{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        try:
            # Kirim request normal
            res = self.session.get(self.target, timeout=10)
            
            # 1. Cek Cookies (Vektor serangan paling umum)
            print(f"{Fore.YELLOW}[+] Analyzing Cookies for Serialized Data...{Style.RESET_ALL}")
            if res.cookies:
                for cookie in res.cookies:
                    # Cek Raw Value
                    self.analyze_data(cookie.value, f"Cookie ({cookie.name})")
                    
                    # Cek jika value adalah Base64, decode lalu cek lagi
                    if self.is_base64(cookie.value):
                        try:
                            decoded = base64.b64decode(cookie.value).decode('utf-8', errors='ignore')
                            self.analyze_data(decoded, f"Cookie ({cookie.name}) - Decoded")
                        except:
                            pass
            else:
                print(f"   {Fore.WHITE}[-] No cookies found.")

            # 2. Cek Headers
            print(f"{Fore.YELLOW}[+] Analyzing Headers...{Style.RESET_ALL}")
            for key, val in res.headers.items():
                if "content-type" in key.lower():
                    if "application/x-java-serialized-object" in val:
                        print(f"   {Fore.RED}[CRITICAL] Header Content-Type indicates Java Serialization!{Style.RESET_ALL}")
                
                # Cek Custom Headers
                self.analyze_data(val, f"Header ({key})")

            # 3. Cek Body (Hidden Inputs / ViewState)
            print(f"{Fore.YELLOW}[+] Analyzing HTML Body (Hidden Inputs)...{Style.RESET_ALL}")
            # Cari input hidden
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.text, 'html.parser')
            inputs = soup.find_all('input', {'type': 'hidden'})
            
            for inp in inputs:
                val = inp.get('value', '')
                name = inp.get('name', 'unnamed')
                if val:
                    self.analyze_data(val, f"Hidden Input ({name})")

        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")

        print("-" * 60)
        print(f"{Fore.GREEN}[*] Deserialization Detection Completed.{Style.RESET_ALL}")

def run_deserialization_scan(url):
    engine = DeserializationHunter(url)
    engine.run_scan()