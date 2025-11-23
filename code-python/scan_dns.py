import dns.resolver
from colorama import Fore, Style

def run_dns_lookup(host):
    print(f"\n{Fore.CYAN}[*] MODULE START: DNS Infrastructure Mapping{Style.RESET_ALL}")
    print(f"{Fore.WHITE}[*] Target Domain: {Fore.GREEN}{host}")
    print("-" * 60)

    record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA']
    
    for record in record_types:
        try:
            answers = dns.resolver.resolve(host, record)
            print(f"\n{Fore.YELLOW}[+] {record} Records:{Style.RESET_ALL}")
            for rdata in answers:
                print(f"    └── {rdata.to_text()}")
        except dns.resolver.NoAnswer:
            pass # Tidak ada record, skip saja
        except dns.resolver.NXDOMAIN:
            print(f"{Fore.RED}[!] Domain tidak ditemukan/terdaftar.")
            break
        except Exception as e:
            # Error umum (timeout, dll)
            pass

    print("\n" + "-" * 60)
    print(f"{Fore.CYAN}[*] DNS Mapping Completed.{Style.RESET_ALL}")