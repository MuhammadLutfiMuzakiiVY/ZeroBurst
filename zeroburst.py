import sys
import os
import time
import subprocess
import datetime
import threading
import socket
from math import sin

# --- SETUP PATH ---
current_directory = os.path.dirname(os.path.abspath(__file__))
modules_folder = os.path.join(current_directory, 'code-python')

if not os.path.exists(modules_folder):
    print(f"Error: Folder '{modules_folder}' hilang!")
    sys.exit(1)

sys.path.append(modules_folder)

# --- AUTO INSTALLER ---
def install_packages():
    required = [
        'requests', 'colorama', 'dnspython', 'beautifulsoup4', 
        'paramiko', 'PyJWT', 'cryptography', 'pyOpenSSL', 'sslyze', 'rich'
    ]
    try:
        import requests, colorama, dns, bs4, paramiko, jwt, cryptography, OpenSSL, rich
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *required])

install_packages()

# --- IMPORTS ---
from colorama import init as colorama_init
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich.live import Live
from rich.prompt import Confirm

# Import All Modules (Lengkap v55)
try:
    import scan_header, scan_port, scan_geo, scan_dns, scan_robots
    import scan_spider, scan_xss, scan_tech, scan_sqli, scan_sqli_enterprise
    import scan_ssh, scan_jwt, scan_crypto
    import scan_cmd_inject, scan_lfi, scan_ssti
    import scan_subdomain, scan_traversal, scan_open_redirect
    import scan_csrf, scan_xxe, scan_ssrf
    import scan_crawler, scan_param_miner, scan_fuzzer, scan_waf
    import scan_asset, scan_secret, scan_cms, scan_auth, scan_cve
    import scan_smuggling, scan_automation, scan_pro, scan_cache_poison
    import scan_cors, scan_jwt_attack, scan_prototype, scan_deserialization
    import scan_logic, scan_ratelimit, scan_nosql, scan_hpp, scan_graphql
    import scan_upload, scan_admin_finder
    import scan_cloud, scan_api_audit, scan_host_header, scan_supply_chain
    import scan_pwd_reset, scan_auth_logic # NEW MODULE
except ImportError as e:
    pass

colorama_init(autoreset=True)
console = Console()

# --- UI HELPERS ---
def get_rainbow_color(offset):
    t = time.time() * 2 + offset
    r = int(sin(t) * 127 + 128)
    g = int(sin(t + 2) * 127 + 128)
    b = int(sin(t + 4) * 127 + 128)
    return f"rgb({r},{g},{b})"

def get_marquee_text(text, width=60):
    t = int(time.time() * 8)
    padding = " " * width
    full_text = padding + text + padding
    start = t % (len(text) + width)
    display = full_text[start : start + width]
    return display

# --- LAYOUTS ---
def get_header_layout():
    art_text = r"""
███████╗███████╗██████╗  ██████╗ ██████╗ ██╗   ██╗███████╗███████╗██████╗ 
╚══███╔╝██╔════╝██╔══██╗██╔═══██╗██╔══██╗██║   ██║██╔════╝██╔════╝╚════██╗
  ███╔╝ █████╗  ██████╔╝██║   ██║██████╔╝██║   ██║███████╗███████╗ █████╔╝
 ███╔╝  ██╔══╝  ██╔══██╗██║   ██║██╔══██╗██║   ██║╚════██║╚════██║ ╚═══██╗
███████╗███████╗██║  ██║╚██████╔╝██████╔╝╚██████╔╝███████║███████║██████╔╝
╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚═════╝"""
    
    styled_art = Text(art_text, style=get_rainbow_color(0))
    my_name = "DEVELOPED BY MUHAMMAD LUTFI MUZAKI | ETHICAL HACKING PROFESSIONAL | ZEROBURST v55.0 (AUTH LOGIC EDITION)"
    marquee = get_marquee_text(my_name, width=75)
    
    now = datetime.datetime.now().strftime("%H:%M:%S")
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except:
        ip = "127.0.0.1"

    info_text = f"[bold cyan]OPERATOR:[/] root@kali   |   [bold cyan]LHOST:[/] {ip}   |   [bold cyan]CLOCK:[/] [bold yellow]{now}[/]"
    
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_row(styled_art)
    grid.add_row(Text(" "))
    grid.add_row(Panel(Text(marquee, style="bold white on blue", justify="center"), border_style="blue", title="[bold]SYSTEM STATUS[/]", title_align="left"))
    grid.add_row(Text(info_text, justify="center"))
    
    return Panel(grid, style="white on black", border_style=get_rainbow_color(1))

def get_menu_table():
    table = Table(show_header=True, header_style="bold magenta", expand=True, border_style="dim white", title="[bold]FULL ARSENAL (55+ TOOLS)[/]")
    table.add_column("ID", style="bold yellow", width=3, justify="center")
    table.add_column("Module Name", style="bold white")
    table.add_column("Type", justify="center")
    
    # RECONNAISSANCE
    table.add_row("1", "Header Security", "[blue]Recon[/]")
    table.add_row("2", "Port & CVE Scan", "[blue]Recon[/]")
    table.add_row("9", "Tech Fingerprint", "[blue]Recon[/]")
    table.add_row("18", "Subdomain Hunter", "[blue]Recon[/]")
    table.add_row("24", "Deep Crawler", "[blue]Recon[/]")
    table.add_row("25", "Parameter Miner", "[blue]Recon[/]")
    table.add_row("28", "Asset Discovery", "[blue]Recon[/]")
    table.add_row("29", "Secret Files/Git", "[blue]Recon[/]")
    table.add_row("30", "CMS Hunter", "[blue]Recon[/]")
    table.add_row("50", "Admin Finder", "[blue]Recon[/]")
    table.add_row("51", "Supply Chain Audit", "[blue]Recon[/]")
    table.add_row("52", "Cloud Bucket/CDN", "[blue bold]CLOUD[/]")
    
    table.add_section()
    
    # ATTACK & INJECTION
    table.add_row("7", "Manual XSS", "[red]Attack[/]")
    table.add_row("10", "SQLi Heuristic", "[red]Attack[/]")
    table.add_row("15", "Command Inject", "[red]Expert[/]")
    table.add_row("16", "LFI/RFI Scanner", "[red]Expert[/]")
    table.add_row("17", "SSTI Hunter", "[red]Expert[/]")
    table.add_row("20", "Open Redirect", "[red]Expert[/]")
    table.add_row("21", "CSRF Hunter", "[red]Expert[/]")
    table.add_row("22", "XXE Injection", "[red]Expert[/]")
    table.add_row("23", "SSRF Cloud", "[red]Expert[/]")
    table.add_row("42", "Host Header Inj", "[red]Expert[/]")
    table.add_row("53", "API Mass Assign", "[red]Expert[/]")
    table.add_row("54", "Pwd Reset Hijack", "[red]Expert[/]")
    table.add_row("55", "Auth Logic Audit", "[red bold]BYPASS[/]") # NEW
    
    table.add_section()
    
    # INFRA & ADVANCED
    table.add_row("11", "SQLi Enterprise", "[magenta]Audit[/]")
    table.add_row("12", "JWT Inspector", "[magenta]Auth[/]")
    table.add_row("13", "SSH Auditor", "[magenta]Infra[/]")
    table.add_row("27", "WAF Bypass", "[magenta]Evasion[/]")
    table.add_row("31", "Auth & Brute", "[magenta]Login[/]")
    table.add_row("38", "HTTP Smuggling", "[magenta]Audit[/]")
    table.add_row("39", "Cache Poisoning", "[magenta]Audit[/]")
    table.add_row("43", "Deserialization", "[magenta]Audit[/]")
    table.add_row("44", "Logic Auditor", "[magenta]Audit[/]")
    table.add_row("45", "Rate Limit Check", "[magenta]Audit[/]")
    table.add_row("49", "Upload Vuln", "[magenta]Audit[/]")
    
    table.add_section()
    table.add_row("99", "ULTIMATE FULL SCAN", "[bold green blink]ALL-IN-ONE[/]")
    
    return table

def get_input_helper():
    return console.input("\n[bold green]   ➜ SELECT MODULE: [/]")

def get_target_helper():
    target = console.input("[bold green]   ➜ ENTER TARGET (URL/IP): [/]")
    if "http" in target:
        h = target.replace("http://", "").replace("https://", "").split("/")[0]
        u = target
    else:
        h = target
        u = "http://" + target
    return h, u

# --- MODULE MAPPER ---
def get_scan_function_by_id(mod_id):
    mapping = {
        '1': scan_header.run_header_check, '2': scan_port.run_port_scan,
        '3': scan_geo.run_geo_ip, '9': scan_tech.analyze_tech,
        '18': scan_subdomain.run_subdomain_scan, '24': scan_crawler.run_deep_crawl,
        '28': scan_asset.run_asset_scan, '29': scan_secret.run_secret_scan,
        '30': scan_cms.run_cms_scan, '7': scan_xss.run_xss_scan,
        '10': scan_sqli.run_sqli_scan, '15': scan_cmd_inject.run_cmd_scan,
        '16': scan_lfi.run_lfi_scan, '17': scan_ssti.run_ssti_scan,
        '19': scan_traversal.run_traversal_scan, '20': scan_open_redirect.run_redirect_scan,
        '22': scan_xxe.run_xxe_scan, '23': scan_ssrf.run_ssrf_scan,
        '27': scan_waf.run_waf_scan, '31': scan_auth.run_auth_scan,
        '32': scan_cve.run_cve_scan, '38': scan_smuggling.run_smuggling_scan,
        '39': scan_cache_poison.run_cache_scan, '40': scan_cors.run_cors_scan,
        '42': scan_host_header.run_host_header_scan,
        '43': scan_deserialization.run_deserialization_scan,
        '44': scan_logic.run_logic_scan, '45': scan_ratelimit.run_ratelimit_scan,
        '46': scan_nosql.run_nosql_scan, '47': scan_hpp.run_hpp_scan,
        '48': scan_graphql.run_graphql_scan, '49': scan_upload.run_upload_scan,
        '50': scan_admin_finder.run_admin_scan,
        '51': scan_supply_chain.run_supply_scan,
        '52': scan_cloud.check_cloud_buckets,
        '53': scan_api_audit.run_api_audit,
        '54': scan_pwd_reset.run_reset_scan,
        '55': scan_auth_logic.run_auth_logic_scan # NEW
    }
    return mapping.get(mod_id)

# --- ULTIMATE SCAN ---
def run_ultimate_scan(host, url):
    console.clear()
    console.print(Panel("[bold green blink]INITIATING ZERO-BURST FINAL SCAN...[/]", border_style="red"))
    
    scan_waf.run_waf_scan(url)
    scan_port.run_port_scan(host)
    scan_tech.analyze_tech(url)
    scan_cloud.check_cloud_buckets(host)
    scan_supply_chain.run_supply_scan(url)
    scan_secret.run_secret_scan(url)
    scan_cms.run_cms_scan(url)
    scan_cve.run_cve_scan(host)
    
    console.print("\n[bold yellow]---------------------------------------------------[/]")
    if Confirm.ask("[bold red]LAUNCH ACTIVE ATTACK PHASE? [/]"):
        scan_host_header.run_host_header_scan(url)
        scan_api_audit.run_api_audit(url)
        scan_auth.run_auth_scan(url)
        scan_auth_logic.run_auth_logic_scan(url) # NEW
        scan_pwd_reset.run_reset_scan(url)
        scan_ssrf.run_ssrf_scan(url)
        scan_xxe.run_xxe_scan(url)
        scan_sqli.run_sqli_scan(url)
        scan_cmd_inject.run_cmd_scan(url)
        scan_lfi.run_lfi_scan(url)
        
    console.print(Panel("[bold green]MISSION ACCOMPLISHED.[/]", border_style="green"))

# --- MAIN LOOP ---
def main_menu():
    layout = Layout()
    while True:
        with Live(layout, refresh_per_second=10, screen=True) as live:
            while True:
                layout.split_column(Layout(name="header", size=14), Layout(name="body"))
                layout["header"].update(get_header_layout())
                layout["body"].update(Align.center(get_menu_table()))
                try: pass 
                except KeyboardInterrupt: break
                break 

        console.clear()
        console.print(get_header_layout())
        console.print(Align.center(get_menu_table()))
        
        console.print("\n[dim italic](System Online...)[/]")
        choice = get_input_helper()

        func = get_scan_function_by_id(choice)
        if func:
            h, u = get_target_helper()
            try: func(u) 
            except: 
                try: func(h) 
                except: console.print("[bold red][!] Error executing module.[/]")
        
        # Other tools
        elif choice == '4': h, _ = get_target_helper(); scan_dns.run_dns_lookup(h)
        elif choice == '5': _, u = get_target_helper(); scan_robots.run_robots_check(u)
        elif choice == '6': _, u = get_target_helper(); scan_spider.run_spider(u)
        elif choice == '8': 
            _, u = get_target_helper()
            t = scan_spider.run_spider(u, True)
            if t: [scan_xss.run_xss_scan(x) for x in t]
        elif choice == '12':
            t = console.input("[bold green]   ➜ TOKEN: [/]"); scan_jwt.analyze_token(t)
        elif choice == '13': t, _ = get_target_helper(); scan_ssh.audit_ssh(t)
        elif choice == '26':
            u = console.input("[bold green]   ➜ URL (FUZZ): [/]"); scan_fuzzer.run_fuzzing_attack(u)
        elif choice == '33':
            f = console.input("[bold green]   ➜ FILE: [/]"); m = console.input("[bold green]   ➜ MOD ID: [/]")
            if get_scan_function_by_id(m): scan_automation.run_multi_target(f, get_scan_function_by_id(m))
        elif choice == '34':
            _, u = get_target_helper(); m = console.input("[bold green]   ➜ MOD ID: [/]")
            if get_scan_function_by_id(m): scan_automation.run_scheduler(u, get_scan_function_by_id(m))
        elif choice == '35': scan_pro.run_ai_fuzzer("")
        elif choice == '36': _, u = get_target_helper(); scan_pro.generate_exploit(u)
        elif choice == '37': scan_pro.configure_notifications()
        elif choice == '41': t = console.input("[bold green]   ➜ TOKEN: [/]"); scan_jwt_attack.run_jwt_attack(t)
        
        elif choice == '99':
            h, u = get_target_helper(); run_ultimate_scan(h, u)
        elif choice == '0':
            sys.exit()
        
        console.input("\n[bold white on blue] Press Enter... [/]")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        sys.exit()