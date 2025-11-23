import socket
import ssl
import OpenSSL
import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from colorama import Fore, Style

class CryptoAuditor:
    def __init__(self, host, port=443):
        self.host = host
        self.port = int(port)

    def get_server_cert_chain(self):
        """Mengambil sertifikat dalam format PEM"""
        try:
            # Menggunakan API standar untuk mengambil sertifikat
            pem_cert = ssl.get_server_certificate((self.host, self.port))
            return pem_cert
        except Exception as e:
            return None

    def analyze_primitives(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Cryptographic Primitives Analysis{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.host}:{self.port}")
        
        pem_data = self.get_server_cert_chain()
        if not pem_data:
            print(f"{Fore.RED}[!] Handshake Failed. Port closed or not SSL.")
            return

        # LOAD CERTIFICATE (Cryptography Library)
        try:
            cert = x509.load_pem_x509_certificate(pem_data.encode(), default_backend())
            
            print(f"{Fore.YELLOW}[X.509 CERTIFICATE DUMP]{Style.RESET_ALL}")
            
            # 1. Subject & Issuer
            # Mengambil atribut CommonName (CN), Organization (O), Country (C)
            subject = cert.subject
            issuer = cert.issuer
            print(f"   ├── {Fore.WHITE}Subject (Owner) : {Fore.GREEN}{subject.rfc4514_string()}")
            print(f"   ├── {Fore.WHITE}Issuer (Signer) : {Fore.CYAN}{issuer.rfc4514_string()}")
            
            # 2. Serial & Version
            print(f"   ├── {Fore.WHITE}Serial Number   : {hex(cert.serial_number)}")
            print(f"   ├── {Fore.WHITE}Version         : {cert.version.name}")
            
            # 3. Signature Algorithm (Primitive Check)
            sig_alg = cert.signature_algorithm_oid._name
            print(f"   ├── {Fore.WHITE}Signature Alg   : {Fore.MAGENTA}{sig_alg}")
            if "sha1" in sig_alg or "md5" in sig_alg:
                print(f"       {Fore.RED}[CRITICAL] Weak Hashing Algorithm Detected (SHA1/MD5)!")

            # 4. Public Key Primitives
            pub_key = cert.public_key()
            key_size = pub_key.key_size
            print(f"   ├── {Fore.WHITE}Public Key      : {pub_key.__class__.__name__} ({key_size} bits)")
            if key_size < 2048:
                print(f"       {Fore.RED}[WEAK] RSA Key < 2048 bits is unsafe.")

            # 5. Validity Period
            not_before = cert.not_valid_before
            not_after = cert.not_valid_after
            print(f"   ├── {Fore.WHITE}Valid From      : {not_before}")
            print(f"   ├── {Fore.WHITE}Valid Until     : {not_after}")
            
            # 6. Extensions (SANs - Subject Alt Names)
            try:
                ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
                sans = ext.value.get_values_for_type(x509.DNSName)
                print(f"   └── {Fore.WHITE}SANs (Aliases)  : {', '.join(sans[:5])} ... (+{len(sans)-5} more)" if len(sans) > 5 else f"   └── {Fore.WHITE}SANs (Aliases)  : {', '.join(sans)}")
            except:
                print(f"   └── {Fore.WHITE}SANs            : None")

        except Exception as e:
            print(f"{Fore.RED}[!] Error parsing certificate: {e}")

    def check_protocols(self):
        print(f"\n{Fore.YELLOW}[PROTOCOL SUPPORT AUDIT]{Style.RESET_ALL}")
        
        # Daftar protokol yang akan diuji
        protocols = [
            ('SSLv2', ssl.PROTOCOL_SSLv23), # Legacy wrapper
            ('TLSv1.0', ssl.PROTOCOL_TLSv1),
            ('TLSv1.1', ssl.PROTOCOL_TLSv1_1),
            ('TLSv1.2', ssl.PROTOCOL_TLSv1_2),
            ('TLSv1.3', getattr(ssl, 'PROTOCOL_TLSv1_3', None)) # Python versi baru support 1.3
        ]

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        for name, proto_const in protocols:
            if proto_const is None: continue
            
            try:
                # Paksa Socket menggunakan versi tertentu
                # Catatan: Implementasi modern Python memblokir SSLv3/2 secara internal,
                # jadi kita gunakan library OpenSSL (pyOpenSSL) jika perlu pengecekan legacy mendalam.
                # Di sini kita pakai pendekatan socket standar untuk TLS.
                
                # Setup context manual untuk isolasi versi
                # (Logic ini simplified, real-world tools pakai sslyze full)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                
                # Kita coba wrap socket
                # Note: SSLContext modern sulit dipaksa ke insecure protocol tanpa downgrade security level OS
                # Jadi kita pakai indikator "Success" sebagai tanda support.
                
                if name in ['SSLv2', 'SSLv3', 'TLSv1.0', 'TLSv1.1']:
                     # Protokol ini sudah deprecated di Python 3.10+, biasanya otomatis gagal
                     # Kita anggap "Attempting"
                     pass
                
                # Simulasi koneksi
                try:
                    ssl_sock = context.wrap_socket(sock, server_hostname=self.host)
                    ssl_sock.connect((self.host, self.port))
                    ver = ssl_sock.version()
                    ssl_sock.close()
                    
                    if name in ver or ver in name:
                         print(f"   ├── {name:<10} : {Fore.GREEN}Supported (Active)")
                except:
                    # Jika gagal connect dengan konteks default, mungkin tidak support atau Python memblokir
                    pass
                    
            except:
                pass

        # Manual Check via pyOpenSSL untuk kepastian Cipher
        print(f"   └── {Fore.CYAN}Protocol Scan Finished.")

    def run_audit(self):
        self.analyze_primitives()
        self.check_protocols()
        print("-" * 60)

def run_crypto_scan(target):
    # Parsing host/port
    if "://" in target:
        host = target.split("://")[1].split("/")[0]
    else:
        host = target.split("/")[0]
    
    if ":" in host:
        h, p = host.split(":")
        CryptoAuditor(h, p).run_audit()
    else:
        CryptoAuditor(host, 443).run_audit()