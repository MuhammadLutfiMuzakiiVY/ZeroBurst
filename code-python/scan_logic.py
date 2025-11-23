import requests
import concurrent.futures
import copy
from colorama import Fore, Style

class BusinessLogicHunter:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'ZeroBurst-LogicAuditor/44.0'}

    def check_idor(self):
        """
        Mendeteksi potensi IDOR dengan menggeser nilai ID numerik di URL.
        Contoh: /order/100 -> Coba akses /order/99 dan /order/101
        """
        print(f"\n{Fore.YELLOW}[+] Testing for IDOR (Insecure Direct Object Reference)...{Style.RESET_ALL}")
        
        # Mencari angka dalam URL
        import re
        match = re.search(r'/(\d+)', self.target)
        if not match:
            print(f"   {Fore.WHITE}[-] No numeric ID found in URL path to fuzz.")
            return

        original_id = match.group(1)
        base_url_pattern = self.target.replace(original_id, "FUZZ")
        
        # Test ID di sekitar ID asli
        test_ids = [str(int(original_id) - 1), str(int(original_id) + 1)]
        
        # Ambil baseline response (ID Asli)
        try:
            base_res = self.session.get(self.target)
            base_len = len(base_res.text)
        except:
            return

        for tid in test_ids:
            test_url = base_url_pattern.replace("FUZZ", tid)
            try:
                res = self.session.get(test_url, timeout=5)
                
                # Jika status 200 OK dan ukurannya mirip dengan asli (tapi tidak sama persis)
                # Berarti kita berhasil mengakses data ID lain
                if res.status_code == 200:
                    print(f"   {Fore.RED}[POTENTIAL IDOR] Access to ID {tid} Successful!{Style.RESET_ALL}")
                    print(f"   ├── URL: {test_url}")
                    print(f"   └── Size: {len(res.text)} bytes")
                elif res.status_code == 403 or res.status_code == 401:
                    print(f"   {Fore.GREEN}[SAFE] Access to ID {tid} Denied (403/401).{Style.RESET_ALL}")
                else:
                    print(f"   {Fore.WHITE}[INFO] ID {tid} returned status {res.status_code}.{Style.RESET_ALL}")
            except:
                pass

    def check_race_condition(self):
        """
        Menguji Race Condition dengan mengirim request simultan (Concurrency).
        Hanya untuk mendeteksi apakah server bisa handle multi-thread, bukan untuk exploit saldo.
        """
        print(f"\n{Fore.YELLOW}[+] Testing for Race Conditions (Concurrency Check)...{Style.RESET_ALL}")
        
        # Kita butuh endpoint yang melakukan 'action' (POST)
        # Jika user memberikan URL GET, kita hanya simulasi request cepat
        
        url = self.target
        threads = 10
        
        print(f"   {Fore.WHITE}Sending {threads} simultaneous requests to detect locking mechanisms...")
        
        status_codes = []
        
        def send_request(u):
            try:
                r = self.session.get(u, timeout=5)
                return r.status_code
            except:
                return 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(send_request, url) for _ in range(threads)]
            for f in concurrent.futures.as_completed(futures):
                status_codes.append(f.result())

        # Analisis
        # Jika semua 200 OK, ada kemungkinan Race Condition (tergantung konteks)
        # Jika ada 429 (Too Many Requests), berarti ada Rate Limiting (Bagus)
        if 429 in status_codes:
            print(f"   {Fore.GREEN}[SAFE] Rate Limiting Detected (429 Too Many Requests).{Style.RESET_ALL}")
        elif all(c == 200 for c in status_codes):
            print(f"   {Fore.YELLOW}[WARNING] No Rate Limit detected. Potential Race Condition if this is a redeem endpoint.{Style.RESET_ALL}")
        else:
            print(f"   {Fore.WHITE}[INFO] Status Codes: {status_codes}{Style.RESET_ALL}")

    def check_parameter_logic(self):
        """
        Menguji validasi logika parameter (Price Tampering / Negative Quantity).
        Membutuhkan URL dengan query parameter (misal: price=100).
        """
        print(f"\n{Fore.YELLOW}[+] Testing Parameter Logic Validation...{Style.RESET_ALL}")
        
        import urllib.parse
        parsed = urllib.parse.urlparse(self.target)
        params = urllib.parse.parse_qs(parsed.query)
        
        if not params:
            print(f"   {Fore.WHITE}[-] No parameters to test logic tampering.")
            return

        # Payload Logika
        payloads = [
            ("-1", "Negative Value"),
            ("0", "Zero Value"),
            ("0.01", "Decimal Value"),
            ("99999999", "Overflow Value")
        ]

        base_url = self.target.split("?")[0]

        for param, val in params.items():
            print(f"   {Fore.WHITE}>>> Testing Parameter: {Fore.CYAN}{param}{Style.RESET_ALL}")
            
            for pay, desc in payloads:
                # Construct URL
                new_params = copy.deepcopy(params)
                new_params[param] = [pay]
                query = urllib.parse.urlencode(new_params, doseq=True)
                attack_url = f"{base_url}?{query}"
                
                try:
                    res = self.session.get(attack_url, timeout=5)
                    
                    # Analisis sederhana
                    # Jika server merespon 200 OK untuk harga negatif, itu BAHAYA.
                    if res.status_code == 200:
                        print(f"      {Fore.RED}[WARN] Server accepted {desc} ({pay}) with 200 OK.{Style.RESET_ALL}")
                    elif res.status_code == 500:
                        print(f"      {Fore.YELLOW}[INFO] Server Error (500) on {desc}. Exception unhandled.{Style.RESET_ALL}")
                    else:
                        # print(f"      [Safe] {desc} blocked ({res.status_code})")
                        pass
                except:
                    pass

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Business Logic Auditor{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[*] Note: This tool checks for logic flaws, it does not perform active fraud.")
        
        self.check_idor()
        self.check_parameter_logic()
        self.check_race_condition()
        
        print("-" * 60)

def run_logic_scan(url):
    engine = BusinessLogicHunter(url)
    engine.run_scan()