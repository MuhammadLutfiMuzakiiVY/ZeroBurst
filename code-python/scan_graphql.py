import requests
import json
from colorama import Fore, Style

class GraphQLHunter:
    def __init__(self, target_url):
        self.target = target_url.split("?")[0]
        self.base_url = "/".join(self.target.split("/")[:3]) # Ambil http://site.com
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'ZeroBurst-GraphQLHunter/48.0',
            'Content-Type': 'application/json'
        }
        
        # Common Endpoints
        self.endpoints = [
            "/graphql", "/api/graphql", "/v1/graphql", "/graph", 
            "/graphql/console", "/hasura/graphql", "/playground"
        ]

    def check_introspection(self, url):
        """Mencoba melakukan dump schema via Introspection"""
        # Query Introspection Standar
        query = """
        query {
          __schema {
            types {
              name
              kind
            }
          }
        }
        """
        payload = {'query': query}
        
        try:
            res = self.session.post(url, json=payload, timeout=5)
            
            if res.status_code == 200 and "data" in res.json() and "__schema" in res.json()['data']:
                print(f"   {Fore.RED}[CRITICAL] INTROSPECTION ENABLED!{Style.RESET_ALL}")
                
                # Hitung jumlah Type yang bocor
                types = res.json()['data']['__schema']['types']
                count = len(types)
                print(f"   ├── URL      : {url}")
                print(f"   ├── Exposure : {count} Data Types exposed (Users, Products, etc).")
                print(f"   └── Impact   : Full Database Schema Mapping possible.")
                
                # Tampilkan sampel data sensitive
                sensitive = ['User', 'Account', 'Password', 'Admin', 'Token', 'Auth']
                found_sens = [t['name'] for t in types if any(s in t['name'] for s in sensitive)]
                if found_sens:
                    print(f"   └── Interesting Types: {Fore.YELLOW}{', '.join(found_sens[:5])}...{Style.RESET_ALL}")
                
                return True
        except:
            pass
        return False

    def check_graphiql(self, url):
        """Mengecek apakah IDE GraphiQL terbuka"""
        try:
            res = self.session.get(url, timeout=5)
            if "GraphiQL" in res.text or "graphql-playground" in res.text:
                print(f"   {Fore.YELLOW}[WARNING] GraphiQL IDE Exposed at {url}{Style.RESET_ALL}")
                print("   └── Developer console is accessible by public.")
                return True
        except:
            pass
        return False

    def run_scan(self):
        print(f"\n{Fore.CYAN}[*] MODULE START: GraphQL Injection & Introspection Hunter{Style.RESET_ALL}")
        print(f"{Fore.WHITE}[*] Target Base: {Fore.GREEN}{self.base_url}")
        print(f"{Fore.WHITE}[*] Scanning Common GraphQL Endpoints...")
        
        found_endpoint = False
        
        for path in self.endpoints:
            full_url = f"{self.base_url}{path}"
            
            # Cek keberadaan endpoint (GET/POST)
            try:
                # Cek IDE dulu (GET)
                self.check_graphiql(full_url)
                
                # Cek API (POST)
                # Kirim query kosong {} untuk melihat respon error standar GraphQL
                res = self.session.post(full_url, json={}, timeout=5)
                
                # Jika respon JSON dan ada error syntax, berarti ini endpoint GraphQL valid
                if res.status_code in [200, 400] and "errors" in res.text:
                    print(f"\n{Fore.GREEN}[+] GraphQL Endpoint Found: {full_url}{Style.RESET_ALL}")
                    found_endpoint = True
                    
                    # Lakukan serangan Introspection
                    is_vuln = self.check_introspection(full_url)
                    
                    if not is_vuln:
                        print(f"   {Fore.GREEN}[SAFE] Introspection query was blocked/disabled.{Style.RESET_ALL}")
                        
            except Exception as e:
                pass

        if not found_endpoint:
            print(f"\n{Fore.WHITE}[-] No GraphQL endpoints discovered on standard paths.{Style.RESET_ALL}")
        
        print("-" * 60)

def run_graphql_scan(url):
    engine = GraphQLHunter(url)
    engine.run_scan()