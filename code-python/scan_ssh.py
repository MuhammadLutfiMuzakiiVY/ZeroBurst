import paramiko
import socket
from colorama import Fore, Style

def audit_ssh(host, port=22, username=None, password=None):
    print(f"\n{Fore.CYAN}[*] MODULE START: SSH Automation & Auditor{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{host}:{port}")
    print("-" * 60)

    client = paramiko.SSHClient()
    # Auto-add host key (PENTING: agar tidak error "Unknown Host" saat scanning)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 1. BANNER GRABBING (Tanpa Login)
        print(f"{Fore.YELLOW}[1] Attempting Banner Grab...{Style.RESET_ALL}")
        # Kita pakai socket biasa dulu untuk ambil banner mentah
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, int(port)))
        banner = sock.recv(1024).decode().strip()
        sock.close()
        
        print(f"   └── SSH Banner : {Fore.MAGENTA}{banner}")
        
        # Cek versi usang (Simple check)
        if "SSH-1" in banner:
            print(f"       {Fore.RED}[CRITICAL] SSH v1 Detected (Insecure!)")
        elif "OpenSSH" in banner:
            print(f"       {Fore.GREEN}[INFO] OpenSSH Detected.")

        # 2. AUTHENTICATION TEST (Jika username/pass diberikan)
        if username and password:
            print(f"\n{Fore.YELLOW}[2] Testing Credentials ({username}/{password})...{Style.RESET_ALL}")
            try:
                client.connect(hostname=host, port=int(port), username=username, password=password, timeout=5)
                print(f"   └── {Fore.GREEN}[SUCCESS] Login Berhasil! Access Granted.")
                
                # 3. REMOTE EXECUTION (Contoh: id & uname -a)
                print(f"\n{Fore.YELLOW}[3] Executing Recon Commands...{Style.RESET_ALL}")
                commands = ["id", "uname -a", "whoami"]
                
                for cmd in commands:
                    stdin, stdout, stderr = client.exec_command(cmd)
                    output = stdout.read().decode().strip()
                    print(f"   {Fore.CYAN}root@{host}:~# {cmd}")
                    print(f"   {Fore.WHITE}{output}")
                
                client.close()
                
            except paramiko.AuthenticationException:
                print(f"   └── {Fore.RED}[FAILED] Authentication Failed (Wrong Credentials).")
            except Exception as e:
                print(f"   └── {Fore.RED}[ERROR] Connection Error: {e}")
        else:
            print(f"\n{Fore.WHITE}[INFO] No credentials provided. Skipping Auth Test & Exec.")

    except socket.timeout:
        print(f"{Fore.RED}[!] Connection Timeout. Host down or filtered.")
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}")

    print("-" * 60)