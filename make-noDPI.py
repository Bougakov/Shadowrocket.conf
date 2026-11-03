#!/usr/bin/env python3
"""Derive RU-noDPI.conf from RU.conf, so the home-WiFi variant never drifts again.

  make-noDPI.py RU.conf > RU-noDPI.conf

RU-noDPI.conf is for home WiFi, where nfqws2 on the Keenetic defeats the YouTube DPI block. 
Only YouTube changes; everything else stays on VPN, because Instagram, X, BBC etc. are NOT fixed by nfqws2 
(IP-blocked or no strategy works). 
Every edit below must match exactly once, so a restructured RU.conf fails loudly instead of silently.
"""
import sys

YT_FILTER = 'policy-regex-filter=(?!.*зарубеж)(?!.*реклама)(?!.*Белые)(?!.*белые)(?!.*Обход)(?!.*БС)(YouTube|Россия|Russia|🇷🇺|🍿|❤)'

EDITS = [
    # [General]: a plain-UDP resolver (8.8.8.8 at least) is intercepted on home ISP's DPI and answers NXDOMAIN for YouTube.
    # Through a proxy that never mattered (the node resolves); for DIRECT YouTube it does. Keep encrypted DNS only.
    ('dns-server = tls://[2606:4700:4700::1112]:853,tls://[2606:4700:4700::1002]:853,tls://1.1.1.2:853,tls://1.0.0.2:853,https://security.cloudflare-dns.com/dns-query,https://dns.google/dns-query,1.1.1.2,1.0.0.2,2606:4700:4700::1112,2606:4700:4700::1002,8.8.8.8,8.8.4.4,2001:4860:4860::8888,2001:4860:4860::8844\n',
     '# noDPI: encrypted resolvers only. Plain DNS is intercepted by home ISP (NXDOMAIN for YouTube), which would break DIRECT YouTube.\n'
     'dns-server = tls://[2606:4700:4700::1112]:853,tls://[2606:4700:4700::1002]:853,tls://1.1.1.2:853,tls://1.0.0.2:853,https://security.cloudflare-dns.com/dns-query,https://dns.google/dns-query\n'),
    # No working IPv6 on the home WiFi, and nfqws2 runs on iptables (IPv4) only: DIRECT YouTube must go out over IPv4.
    ('prefer-ipv6 = true\n',
     '# noDPI: the home line has no working IPv6 and nfqws2 treats IPv4 only\n'
     'prefer-ipv6 = false\n'),

    # [Proxy Group]: YouTube goes DIRECT (nfqws2 on the router), and falls back to the VPN pool when the direct probe fails
    # (nfqws2 down, router reset, or this config used away from home).
    (f'YOUTUBE-GROUP = url-test,{YT_FILTER},',
     f'YOUTUBE-VPN = url-test,{YT_FILTER},'),
    ('url=https://www.youtube.com/robots.txt\n',
     'url=https://www.youtube.com/robots.txt\n'
     '# noDPI: DIRECT first (nfqws2 on the home router), YOUTUBE-VPN only if the direct probe fails\n'
     'YOUTUBE-GROUP = fallback,DIRECT,YOUTUBE-VPN,interval=120,timeout=5,url=https://www.youtube.com/robots.txt\n'),
    ('# Fallback if a group has been circumvented by DPI bypass (home network):\n'
     '# INSTAGRAM-GROUP = random,DIRECT,interval=120,timeout=5,url=http://www.gstatic.com/generate_204\n', ''),

    # [Rule]: YouTube rules outside the router's nfqws2 hostlist (lists/user.list) would fail DIRECT; pin them to the VPN.
    # Raw-IP connections can't be matched by a hostlist at all.
    ('IP-CIDR,172.110.32.0/21,YOUTUBE-GROUP,no-resolve\n',
     '# noDPI: not in the nfqws2 hostlist, so these stay on VPN\n'
     'IP-CIDR,172.110.32.0/21,YOUTUBE-VPN,no-resolve\n'),
    ('IP-CIDR,216.73.80.0/20,YOUTUBE-GROUP,no-resolve\n', 'IP-CIDR,216.73.80.0/20,YOUTUBE-VPN,no-resolve\n'),
    ('IP-CIDR,2620:120:e000::/40,YOUTUBE-GROUP,no-resolve\n', 'IP-CIDR,2620:120:e000::/40,YOUTUBE-VPN,no-resolve\n'),
    ('DOMAIN-SUFFIX,yt.be,YOUTUBE-GROUP\n', 'DOMAIN-SUFFIX,yt.be,YOUTUBE-VPN\n'),
    ('DOMAIN-SUFFIX,video.google.com,YOUTUBE-GROUP\n', 'DOMAIN-SUFFIX,video.google.com,YOUTUBE-VPN\n'),
    ('DOMAIN-SUFFIX,gvt2.com,YOUTUBE-GROUP\n', 'DOMAIN-SUFFIX,gvt2.com,YOUTUBE-VPN\n'),
]

text = open(sys.argv[1], encoding='utf-8').read()
for old, new in EDITS:
    n = text.count(old)
    if n != 1:
        sys.exit(f'make-noDPI: expected exactly 1 match, found {n}: {old[:80]!r}')
    text = text.replace(old, new)

sys.stdout.write('# GENERATED from RU.conf by make-noDPI.py: edit RU.conf, then regenerate. Home WiFi with nfqws2: YouTube DIRECT.\n' + text)
