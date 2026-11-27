#!/usr/bin/env python3
import ipaddress, json, re, urllib.request
from pathlib import Path

SOURCES = {
  "dlisin_proxy": "https://raw.githubusercontent.com/dlisin/shadowrocket-config/master/proxy.list",
  "dlisin_direct": "https://raw.githubusercontent.com/dlisin/shadowrocket-config/master/direct.list",
  "dlisin_reject": "https://raw.githubusercontent.com/dlisin/shadowrocket-config/master/reject.list",
  "misha_domains": "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domains_community.list",
  "misha_domain_ips": "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/domain_ips.list",
  "misha_voice_ports": "https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/main/rules/voice_ports.list",
  "blackmatrix_apple": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Apple/Apple.list",
  "blackmatrix_discord": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Discord/Discord.list",
  "blackmatrix_facebook": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Facebook/Facebook.list",
  "blackmatrix_instagram": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Instagram/Instagram.list",
  "blackmatrix_openai": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/OpenAI/OpenAI.list",
  "blackmatrix_spotify": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Spotify/Spotify.list",
  "blackmatrix_telegram": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Telegram/Telegram.list",
  "blackmatrix_whatsapp": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Whatsapp/Whatsapp.list",
  "blackmatrix_youtube": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/YouTube/YouTube.list",
  "zkeen_meta_ips": "https://github.com/toneywhitez/zkeen_rules/releases/latest/download/meta_ips.list",
  "zkeen_telegram_ips": "https://github.com/toneywhitez/zkeen_rules/releases/latest/download/telegram_ips.list",
  "zkeen_youtube_ips": "https://github.com/toneywhitez/zkeen_rules/releases/latest/download/youtube_ips.list"
}
OUT = Path("dist")
OUT.mkdir(exist_ok=True)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "streisand-dlisin-builder/1.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8-sig", errors="replace")

def varint(n):
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7f) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)

def field_bytes(num, data):
    return varint((num << 3) | 2) + varint(len(data)) + data

def domain_entry(kind, value):
    b = bytearray()
    if kind:
        b += varint(8) + varint(kind)
    b += field_bytes(2, value.encode())
    return bytes(b)

def geosite(tag, entries):
    site = field_bytes(1, tag.encode())
    for kind, value in sorted(entries):
        site += field_bytes(2, domain_entry(kind, value))
    return field_bytes(1, site)

domains = {"proxy": set(), "direct": set()}
ips = {"proxy": set(), "direct": set()}
ports = set()
skipped = {}
errors = []

for name, url in SOURCES.items():
    try:
        content = get(url)
    except Exception as e:
        errors.append(f"{name}: download failed: {e}")
        continue
    target = "direct" if name == "dlisin_direct" else "proxy"
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        rule = parts[0].upper()
        if rule in ("DOMAIN-SUFFIX", "DOMAIN", "DOMAIN-KEYWORD") and len(parts) >= 2:
            value = parts[1].lower().rstrip(".")
            if rule == "DOMAIN-SUFFIX":
                domains[target].add((2, value))   # RootDomain
            elif rule == "DOMAIN":
                domains[target].add((3, value))   # Full
            else:
                # Xray GeoSite has no Shadowrocket keyword enum.
                # Regex equivalent: substring anywhere in the queried domain.
                domains[target].add((1, ".*" + re.escape(value) + ".*"))
        elif rule in ("IP-CIDR", "IP-CIDR6") and len(parts) >= 2:
            try:
                net = ipaddress.ip_network(parts[1], strict=False)
                ips[target].add(str(net))
            except ValueError:
                skipped[rule] = skipped.get(rule, 0) + 1
        elif rule == "DST-PORT" and len(parts) >= 2:
            p = parts[1].replace("\u200b", "").replace("\u200e", "").replace("\ufeff", "").replace("–", "-").replace("—", "-")
            if re.fullmatch(r"\d+(?:-\d+)?", p):
                ports.add(p)
            else:
                skipped[rule] = skipped.get(rule, 0) + 1
        elif rule in ("USER-AGENT", "IP-ASN"):
            skipped[rule] = skipped.get(rule, 0) + 1
        else:
            # zkeen release files may contain bare IPv4/IPv6 addresses or CIDRs.
            try:
                net = ipaddress.ip_network(line, strict=False)
                ips[target].add(str(net))
            except ValueError:
                skipped[rule] = skipped.get(rule, 0) + 1

# Misha's domain_ips.list contains bare IP addresses, not Shadowrocket directives.
try:
    for raw in get(SOURCES["misha_domain_ips"]).splitlines():
        value = raw.strip()
        if value and not value.startswith("#"):
            try:
                ip = ipaddress.ip_address(value)
                ips["proxy"].add(str(ipaddress.ip_network(f"{ip}/{ip.max_prefixlen}", strict=False)))
            except ValueError:
                skipped["INVALID_IP"] = skipped.get("INVALID_IP", 0) + 1
except Exception as e:
    errors.append(f"misha_domain_ips: {e}")

for tag in ("direct", "proxy"):
    (OUT / f"{tag}.txt").write_text("\n".join(
        (("full:" if k == 3 else "regex:" if k == 1 else "domain:") + v)
        for k, v in sorted(domains[tag])
    ) + "\n", encoding="utf-8")

blob = geosite("DIRECT", domains["direct"]) + geosite("PROXY", domains["proxy"])
(OUT / "custom.dat").write_bytes(blob)
(OUT / "proxy-ips.txt").write_text("\n".join(sorted(ips["proxy"], key=lambda x: (ipaddress.ip_network(x).version, int(ipaddress.ip_network(x).network_address), ipaddress.ip_network(x).prefixlen))) + "\n", encoding="utf-8")
(OUT / "direct-ips.txt").write_text("\n".join(sorted(ips["direct"])) + "\n", encoding="utf-8")
(OUT / "proxy-ports.txt").write_text("\n".join(sorted(ports, key=lambda x: int(x.split("-")[0]))) + "\n", encoding="utf-8")
report = {
  "source_count": len(SOURCES), "domains": {k: len(v) for k,v in domains.items()},
  "ip_ranges": {k: len(v) for k,v in ips.items()}, "ports": len(ports),
  "skipped_rules": skipped, "download_errors": errors
}
(OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
# Build a Streisand importable routing profile. Each match dimension is
# a separate rule because Xray combines fields inside one rule with AND.
import base64, plistlib
private_ips = sorted(ips["direct"], key=lambda x: (ipaddress.ip_network(x).version, int(ipaddress.ip_network(x).network_address), ipaddress.ip_network(x).prefixlen))
proxy_ips = sorted(ips["proxy"], key=lambda x: (ipaddress.ip_network(x).version, int(ipaddress.ip_network(x).network_address), ipaddress.ip_network(x).prefixlen))
route_rules = []
if private_ips:
    route_rules.append({"outboundTag":"direct","ip":private_ips})
route_rules.append({"outboundTag":"direct","domain":["ext:custom.dat:direct"]})
route_rules.append({"outboundTag":"proxy","domain":["ext:custom.dat:proxy"]})
if proxy_ips:
    route_rules.append({"outboundTag":"proxy","ip":proxy_ips})
if ports:
    route_rules.append({"outboundTag":"proxy","port":",".join(sorted(ports, key=lambda x: int(x.split("-")[0])))})
route_rules.append({"outboundTag":"direct","domainMatcher":"hybrid"})
route_profile = {
    "name":"dlisin-direct-proxy",
    "uuid":"8E1D3A91-4B67-4F1A-9C22-5B6D2E7A104C",
    "rules":route_rules
}
def write_route_files(profile, stem):
    (OUT / f"{stem}.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    inner = base64.b64encode(plistlib.dumps(profile, fmt=plistlib.FMT_BINARY, sort_keys=False)).decode("ascii")
    uri = "streisand://" + base64.b64encode(("import/route://" + inner).encode("utf-8")).decode("ascii")
    (OUT / f"{stem}.txt").write_text(uri + "\n", encoding="utf-8")

write_route_files(route_profile, "streisand-route")

# Standalone profile: inline domain rules, so no external custom.dat is required.
def inline_domains(items):
    prefixes = {1: "regexp:", 2: "domain:", 3: "full:"}
    return [prefixes[k] + value for k, value in sorted(items)]

standalone_rules = []
if private_ips:
    standalone_rules.append({"outboundTag":"direct","ip":private_ips})
if domains["direct"]:
    standalone_rules.append({"outboundTag":"direct","domain":inline_domains(domains["direct"])})
if domains["proxy"]:
    standalone_rules.append({"outboundTag":"proxy","domain":inline_domains(domains["proxy"])})
if proxy_ips:
    standalone_rules.append({"outboundTag":"proxy","ip":proxy_ips})
if ports:
    standalone_rules.append({"outboundTag":"proxy","port":",".join(sorted(ports, key=lambda x: int(x.split("-")[0])))})
standalone_rules.append({"outboundTag":"direct","domainMatcher":"hybrid"})
standalone_profile = {
    "name":"dlisin-direct-proxy-standalone",
    "uuid":"A71D6C42-93E8-4B17-8D30-6C1F5A92E804",
    "rules":standalone_rules
}
write_route_files(standalone_profile, "streisand-route-standalone")

print(json.dumps(report, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit("One or more required source downloads failed; refusing to publish incomplete data.")
if not domains["proxy"]:
    raise SystemExit("PROXY domain list is empty.")
