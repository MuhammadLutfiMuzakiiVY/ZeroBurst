import requests
import time
import json
import re
import random
import string
from urllib.parse import urlparse, urlencode, parse_qs
from colorama import Fore, Style
import copy

class EnterpriseSQLiAuditor:
    def __init__(self, target_url):
        self.target = target_url
        self.headers = {
            'User-Agent': 'ZeroBurst-Enterprise/9.0',
            'Referer': target_url,
            'Cookie': 'session_id=test_session'
        }
        self.vulnerabilities = []
        self.db_fingerprint = "Unknown"
        
        # MODUL 2.1: DB Error Signatures
        self.db_signatures = {
            'MySQL': [r"SQL syntax.*MySQL", r"Warning.*mysql_.*", r"valid MySQL result", r"MySqlClient\."],
            'PostgreSQL': [r"PostgreSQL.*ERROR", r"Warning.*pg_.*", r"valid PostgreSQL result", r"Npgsql\."],
            'MSSQL': [r"Driver.* SQL[\-\_\ ]*Server", r"OLE DB.* SQL Server", r"(\W|\A)SQL Server.*Driver", r"Warning.*mssql_.*"],
            'Oracle': [r"ORA-[0-9][0-9][0-9][0-9]", r"Oracle error", r"Oracle.*Driver", r"Warning.*oci_.*"],
            'SQLite': [r"SQLite/JDBCDriver", r"SQLite.Exception", r"System.Data.SQLite.SQLiteException"]
        }

    # --- HELPER: Random String ---
    def random_str(self, length=6):
        return ''.join(random.choices(string.ascii_letters, k=length))

    # --- MODUL 2: DB FINGERPRINTING & ERROR TAXONOMY ---
    def check_fingerprint(self, html):
        for db, regexes in self.db_signatures.items():
            for pattern in regexes:
                if re.search(pattern, html, re.IGNORECASE):
                    self.db_fingerprint = db
                    return f"{Fore.RED}[CRITICAL] DB Detected: {db} (Error Leakage)"
        return f"{Fore.GREEN}[SAFE] No DB Error detected."

    # --- MODUL 3: BLIND SQLi (TIME-BASED) ---
    def check_time_based(self, url, param):
        print(f"   {Fore.YELLOW}[Scan] Checking Time-Based Blind SQLi on '{param}'...{Style.RESET_ALL}")
        
        # Payload generik untuk berbagai DB
        payloads = {
            "MySQL": " SLEEP(5) -- ",
            "PostgreSQL": " pg_sleep(5) -- ",
            "MSSQL": " WAITFOR DELAY '0:0:5' -- "
        }
        
        # Baseline request (Normal)
        start = time.time()
        try:
            requests.get(url, headers=self.headers, timeout=10)
        except: return
        latency = time.time() - start
        
        # Jika server lambat, set threshold tinggi
        threshold = max(5, latency + 4) 
        
        for db, payload in payloads.items():
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            params[param] = [params[param][0] + payload]
            
            new_query = urlencode(params, doseq=True)
            attack_url = f"{url.split('?')[0]}?{new_query}"
            
            start_attack = time.time()
            try:
                requests.get(attack_url, headers=self.headers, timeout=15)
            except requests.exceptions.ReadTimeout:
                # Timeout is actually a GOOD sign for time-based SQLi
                pass
                
            duration = time.time() - start_attack
            
            if duration > threshold:
                evidence = {
                    "type": "Time-Based Blind SQLi",
                    "location": f"Parameter: {param}",
                    "payload": payload,
                    "db_guess": db,
                    "response_time": f"{duration:.2f}s (Threshold: {threshold}s)",
                    "severity": "High"
                }
                self.vulnerabilities.append(evidence)
                print(f"      {Fore.RED}[!] TIME ANOMALY DETECTED ({db}) - {duration:.2f}s")
                return

    # --- MODUL 4: HTTP HEADER ATTACKS ---
    def check_headers(self, url):
        print(f"   {Fore.YELLOW}[Scan] Testing HTTP Header Injection...{Style.RESET_ALL}")
        
        headers_to_test = ['User-Agent', 'Referer', 'X-Forwarded-For', 'Cookie']
        payload = "' OR '1'='1"
        
        for header in headers_to_test:
            # Copy headers asli
            attack_headers = self.headers.copy()
            attack_headers[header] = payload
            
            try:
                res = requests.get(url, headers=attack_headers, timeout=5)
                # Cek apakah payload memicu error DB
                fingerprint = self.check_fingerprint(res.text)
                
                if "CRITICAL" in fingerprint:
                    evidence = {
                        "type": "Header Injection",
                        "location": f"Header: {header}",
                        "payload": payload,
                        "severity": "Medium",
                        "details": "Database error triggered via Header"
                    }
                    self.vulnerabilities.append(evidence)
                    print(f"      {Fore.RED}[!] HEADER INJECTION: {header}")
            except:
                pass

    # --- MAIN ENGINE ---
    def run_full_audit(self):
        print(f"\n{Fore.CYAN}[*] STARTING ENTERPRISE AUDIT on {self.target}{Style.RESET_ALL}")
        
        # 1. Parameter Analysis (GET)
        parsed = urlparse(self.target)
        params = parse_qs(parsed.query)
        
        if not params:
            print(f"{Fore.RED}[!] No parameters detected. Trying Header Scan only.")
        
        # Loop Parameters
        for param in params:
            # Test Error Based (Simple)
            print(f"\n{Fore.WHITE}>>> Auditing Parameter: {Fore.GREEN}{param}")
            
            # Injection '
            params_copy = copy.deepcopy(params)
            params_copy[param] = [params_copy[param][0] + "'"]
            attack_url = f"{self.target.split('?')[0]}?{urlencode(params_copy, doseq=True)}"
            
            res = requests.get(attack_url, headers=self.headers)
            fp_result = self.check_fingerprint(res.text)
            print(f"   [Fingerprint] {fp_result}")
            
            if "CRITICAL" in fp_result:
                self.vulnerabilities.append({
                    "type": "Error-Based SQLi",
                    "location": f"Parameter: {param}",
                    "payload": "'",
                    "severity": "Critical",
                    "db_type": self.db_fingerprint
                })
            
            # Test Time Based
            self.check_time_based(self.target, param)

        # 2. Header Analysis
        self.check_headers(self.target)
        
        # 3. REPORTING (MODUL 11)
        self.generate_report()

    def generate_report(self):
        print(f"\n{Fore.CYAN}[*] GENERATING ENTERPRISE REPORT...{Style.RESET_ALL}")
        
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename_json = f"report_zeroburst_{timestamp}.json"
        filename_html = f"report_zeroburst_{timestamp}.html"
        
        # Data Struktur
        report_data = {
            "target": self.target,
            "scan_time": timestamp,
            "total_vulnerabilities": len(self.vulnerabilities),
            "db_fingerprint": self.db_fingerprint,
            "findings": self.vulnerabilities
        }
        
        # Save JSON
        with open(filename_json, "w") as f:
            json.dump(report_data, f, indent=4)
            
        # Save HTML (Simple Dashboard)
        html_template = f"""
        <html>
        <head>
            <title>ZeroBurst Security Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f4f4f4; }}
                h1 {{ color: #2c3e50; }}
                .card {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .critical {{ border-left: 5px solid #e74c3c; }}
                .high {{ border-left: 5px solid #e67e22; }}
                .medium {{ border-left: 5px solid #f1c40f; }}
                pre {{ background: #eee; padding: 10px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <h1>ZeroBurst Enterprise Report</h1>
            <div class="card">
                <h2>Executive Summary</h2>
                <p><strong>Target:</strong> {self.target}</p>
                <p><strong>Date:</strong> {timestamp}</p>
                <p><strong>Database Detected:</strong> {self.db_fingerprint}</p>
                <p><strong>Total Vulnerabilities:</strong> {len(self.vulnerabilities)}</p>
            </div>
            
            <h2>Technical Findings</h2>
            {''.join([f'''
            <div class="card {v['severity'].lower()}">
                <h3>[{v['severity']}] {v['type']}</h3>
                <p><strong>Location:</strong> {v['location']}</p>
                <pre>Payload: {v['payload']}</pre>
                <p><em>Details: {v.get('details', v.get('response_time', ''))}</em></p>
            </div>
            ''' for v in self.vulnerabilities])}
        </body>
        </html>
        """
        
        with open(filename_html, "w") as f:
            f.write(html_template)
            
        print(f"{Fore.GREEN}[SUCCESS] Reports generated:")
        print(f"   ├── JSON: {filename_json}")
        print(f"   └── HTML: {filename_html} (Open this in browser)")

def run_enterprise_scan(url):
    auditor = EnterpriseSQLiAuditor(url)
    auditor.run_full_audit()