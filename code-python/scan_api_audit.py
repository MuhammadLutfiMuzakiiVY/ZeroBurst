import requests
from colorama import Fore, Style

def run_api_audit(url):
    print(f"\n{Fore.CYAN}[*] MODULE START: API Logic & Mass Assignment Auditor{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{url}")
    
    # 1. MASS ASSIGNMENT TEST
    # Mengirimkan parameter terlarang ke endpoint
    print(f"\n{Fore.YELLOW}[+] Testing Mass Assignment (Privilege Escalation)...{Style.RESET_ALL}")
    
    payloads = {
        "role": "admin",
        "is_admin": True,
        "isAdmin": 1,
        "group": "administrator",
        "permissions": "all"
    }
    
    try:
        # Kita asumsikan method POST/PUT. Jika user beri GET, kita ubah jadi POST utk test
        res = requests.post(url, json=payloads, timeout=5)
        
        # Analisis Respon
        # Jika server merespon sukses dan mengembalikan data yang kita kirim, ada potensi bahaya
        if res.status_code in [200, 201]:
            if "admin" in res.text.lower() or "role" in res.text.lower():
                print(f"   {Fore.RED}[WARNING] API accepted admin parameters! (Status: {res.status_code}){Style.RESET_ALL}")
                print(f"   └── Check if user privileges were actually elevated.")
            else:
                print(f"   {Fore.GREEN}[SAFE] Parameters accepted but likely ignored.{Style.RESET_ALL}")
        else:
            print(f"   {Fore.GREEN}[SAFE] Server rejected payload (Status: {res.status_code}).{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"   [!] Error connecting: {e}")

    # 2. OAUTH MISCONFIG CHECK (Passive)
    # Mengecek apakah URL mengandung parameter redirect_uri yang berbahaya
    if "oauth" in url.lower() or "redirect_uri" in url.lower():
        print(f"\n{Fore.YELLOW}[+] OAuth Endpoint Detected! Checking Redirect URI...{Style.RESET_ALL}")
        print(f"   {Fore.CYAN}[INFO] Manual Check Required:{Style.RESET_ALL}")
        print(f"   1. Try changing redirect_uri to attacker.com")
        print(f"   2. Try changing response_type to 'token' (Implicit Flow)")
    
    print("-" * 60)