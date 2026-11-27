# Streisand rules based on dlisin/shadowrocket-config

This repository builds an Xray GeoSite file from the current rule sources referenced by dlisin's upstream `shadowrocket.conf`.

## Scope
- Domain rules are compiled into `custom.dat` with `DIRECT` and `PROXY` categories.
- Shadowrocket `DOMAIN-SUFFIX` maps to Xray RootDomain.
- `DOMAIN` maps to Full.
- `DOMAIN-KEYWORD` maps to a regular expression equivalent that matches the keyword anywhere in the queried domain.
- IP-CIDR/IP-CIDR6 rules and the Misha bare-IP list are exported separately to `proxy-ips.txt` and `direct-ips.txt`.
- DST-PORT rules are exported separately to `proxy-ports.txt`.
- USER-AGENT and IP-ASN cannot be represented faithfully as Xray GeoSite domains and are counted in `report.json`, not silently converted.
- Reject source is currently empty, so no reject category is invented.

## Build
GitHub Actions runs on push, manually, and daily. Successful builds publish `custom.dat` and companion routing lists as assets of the `latest` release.

## Xray route references
- `ext:custom.dat:direct`
- `ext:custom.dat:proxy`

Import `custom.dat` into Streisand's geofiles before using these references. Existing VLESS/Reality outbound nodes are not modified by this repository.
