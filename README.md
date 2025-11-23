# 🚀 ZeroBurst: The Ultimate Penetration Testing Suite (v55.0)



[![Python](https://img.shields.io/badge/Python-3.x-blue)]()

[![License](https://img.shields.io/badge/License-MIT-green)]()

[![Modules](https://img.shields.io/badge/Modules-55%2B%20Active-red)]()

[![Status](https://img.shields.io/badge/Status-FINAL%20ARCHITECT-yellow)]()



## 🎯 Project Overview



**ZeroBurst** is a high-performance, command-line **Application Security Testing (AST)** framework developed by Muhammad Lutfi Muzaki. It consolidates over **55 specialized modules** to efficiently map, audit, and validate the security posture of modern web applications and underlying infrastructure.



The suite is designed for **Ethical Hacking Professionals** and security researchers who require deep, reliable, and automated vulnerability detection—from simple header misconfigurations to complex Server-Side Request Forgery (SSRF) and Deserialization flaws.



---



## ⚔️ The Full Arsenal: Module Matrix (55+ Capabilities)



The ZeroBurst framework organizes its capabilities into four distinct tiers, allowing focused and strategic security assessments.



### I. ATTACK SURFACE MAPPING [RECONNAISSANCE & DISCOVERY]

Focus: Identifying infrastructure, configuration, and vulnerable inputs.



| Category | Features | Description |

| :--- | :--- | :--- |

| **Fingerprinting** | Tech Fingerprint (9), Header Security (1), Asset Discovery (28) | Identifies CMS, Web Server, Frameworks, and scores security headers. |

| **Discovery** | Deep Crawler (24), Parameter Miner (25), Secret File Hunter (29) | Aggressively finds endpoints, hidden inputs, API paths, and exposed `.env`/`.git` files. |

| **Topology** | Port Scanner (2), Subdomain Hunter (18), DNS Mapping (4) | Maps network ports, finds subdomains via brute-force and public DNS records. |

| **Specialized** | Robots.txt (5), CMS Vulnerability (30), Admin Panel Finder (50) | Looks for explicit path exclusions and checks for default WP/Joomla/Drupal files. |



### II. INJECTION & EXPLOITATION [HIGH SEVERITY ATTACKS]

Focus: Testing application logic for flaws that allow unauthorized code execution or data access.



| ID | Vulnerability | Attack Vector Focus |

| :-: | :--- | :--- |

| **15** | RCE | Command Injection (Blind/Reflected) with Evasion techniques. |

| **10** | SQLi Heuristic | Behavioral detection of classic/blind SQL injection flaws. |

| **46** | NoSQL Injection | MongoDB/CouchDB operator testing (`$ne`, `$gt`). |

| **17** | SSTI Hunter | Server-Side Template Injection (Jinja2, Twig, FreeMarker) detection. |

| **16** | LFI/RFI | Local/Remote File Inclusion (Reading `/etc/passwd` or code leak via Wrappers). |

| **23** | SSRF Cloud | Server-Side Request Forgery (Targeting AWS/GCP Metadata & internal resources). |

| **22** | XXE Hunter | XML External Entity Injection (File Read via XML parser). |

| **48** | GraphQL Injection | Introspection Attack to dump database schema. |

| **47** | HPP Attack | HTTP Parameter Pollution (Testing server precedence/concatenation). |



### III. LOGIC, AUDIT & INFRASTRUCTURE [ADVANCED CHECKS]

Focus: Auditing authentication flows, caching mechanisms, and system misconfigurations.



| ID | Module Name | Audit Focus |

| :-: | :--- | :--- |

| **31** | Auth & Brute-Force | Weak Password Dictionary Check & Login Form Analysis. |

| **44** | Logic Auditor | Testing for IDOR, Race Conditions, and price tampering. |

| **54** | Pwd Reset Hijack | Host Header Poisoning & Token Leakage in Password Reset Flow. |

| **38** | HTTP Smuggling | Checks for CL.TE / TE.CL desynchronization using time-delay. |

| **40** | CORS Misconfig | Audits strictness of Cross-Origin Resource Sharing policy. |

| **32** | CVE DB Mapping | Maps detected services to known high-profile Common Vulnerabilities and Exposures. |

| **27** | WAF Bypass Hunter | Automated payload mutation against blocking status codes (403/406). |

| **39** | Cache Poisoning | Unkeyed Input Reflection Analysis (Front-End/CDN Vulnerability). |

| **49** | Upload Vuln | Checks File Upload Endpoints for extension filtering weaknesses. |



---



## ⚙️ Usage Workflow



### 🚀 Installation



ZeroBurst requires Python 3.8+ and runs best within a dedicated Virtual Environment (`venv`).



```bash

# 1. Clone the repository

git clone [https://github.com/MuhammadLutfiMuzakiiVY/ZeroBurst.git](https://github.com/MuhammadLutfiMuzakiiVY/ZeroBurst.git)



# 2. Setup environment and dependencies

cd ZeroBurst

python -m venv venv

source venv/bin/activate 

pip install -r requirements.txt 



# 3. Run the framework

python zeroburst.py,
