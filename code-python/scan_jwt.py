import jwt
import datetime
from colorama import Fore, Style

def analyze_token(token_str):
    print(f"\n{Fore.CYAN}[*] MODULE START: JWT Inspector & Analyzer{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Token Length: {len(token_str)} chars")
    print("-" * 60)

    try:
        # Bersihkan spasi/bearer
        if token_str.lower().startswith("bearer "):
            token_str = token_str.split(" ")[1]

        # 1. DECODE HEADER (Unverified)
        header = jwt.get_unverified_header(token_str)
        print(f"{Fore.YELLOW}[HEADER ANALYSIS]{Style.RESET_ALL}")
        print(f"   ├── Algorithm : {Fore.GREEN}{header.get('alg')}")
        print(f"   ├── Type      : {header.get('typ')}")
        
        # Security Check: Algorithm None Attack
        if header.get('alg') == 'none' or header.get('alg') is None:
            print(f"   └── {Fore.RED}[CRITICAL] VULNERABILITY: 'None' Algorithm Detected! (Auth Bypass Possible)")
        elif header.get('alg') == 'HS256':
            print(f"   └── {Fore.CYAN}[INFO] Symmetric Key (HS256). Prone to Brute-Force if key is weak.")
        elif header.get('alg') == 'RS256':
            print(f"   └── {Fore.CYAN}[INFO] Asymmetric Key (RS256). Check for Key Confusion Attack.")

        # 2. DECODE PAYLOAD (Unverified)
        # Kita gunakan verify=False karena kita (hacker) belum tahu secret key-nya
        payload = jwt.decode(token_str, options={"verify_signature": False})
        
        print(f"\n{Fore.YELLOW}[PAYLOAD DATA]{Style.RESET_ALL}")
        for key, value in payload.items():
            print(f"   ├── {key:<10} : {Fore.WHITE}{value}")
        
        # Security Check: Expiration
        if 'exp' in payload:
            exp_time = datetime.datetime.fromtimestamp(payload['exp'])
            now = datetime.datetime.now()
            print(f"\n{Fore.YELLOW}[TIME VALIDATION]{Style.RESET_ALL}")
            print(f"   ├── Expires At : {exp_time}")
            if now > exp_time:
                print(f"   └── Status     : {Fore.RED}[EXPIRED] Token is no longer valid.")
            else:
                print(f"   └── Status     : {Fore.GREEN}[VALID] Token is active.")

    except jwt.DecodeError:
        print(f"{Fore.RED}[!] Invalid JWT Format. Cannot decode.")
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}")

    print("-" * 60)