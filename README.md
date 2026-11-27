# Streisand rules based on dlisin/shadowrocket-config

This repository builds an Xray GeoSite database and a minimal Xray routing fragment from the current rule sources referenced by dlisin's upstream shadowrocket.conf.

## Outputs
- dist/custom.dat: GeoSite database with DIRECT and PROXY domain categories.
- dist/streisand-route.json: Xray routing fragment. It uses the existing outbound tags `direct` and `proxy`; it does not create or modify VLESS/Reality nodes.
- dist/proxy-ips.txt and dist/direct-ips.txt: source IP ranges kept outside GeoSite.
- dist/proxy-ports.txt: proxy destination ports.
- dist/report.json: source counts, skipped rule types, and download errors.

## Rule translation
- DOMAIN-SUFFIX becomes Xray RootDomain.
- DOMAIN becomes Xray Full.
- DOMAIN-KEYWORD becomes a regex that matches the keyword anywhere in the queried domain.
- IP-CIDR/IP-CIDR6 and Misha's bare IP list are kept as IP route rules.
- DST-PORT is kept as a port route rule. Invisible Unicode characters and en dashes in ranges are normalized.
- USER-AGENT and IP-ASN cannot be represented as domain or IP-CIDR rules by this builder. They are reported as skipped rather than silently misrepresented.
- The upstream reject.list is empty at the time of the latest build, so no reject rule is invented.

## Routing order
1. Private IPv4 ranges from dlisin direct.list go DIRECT.
2. ext:custom.dat:direct goes DIRECT (currently includes keenetic.link).
3. ext:custom.dat:proxy goes PROXY.
4. Explicit service IP ranges and destination ports go PROXY.
5. Remaining TCP/UDP traffic goes DIRECT.

The generated route fragment uses domainStrategy IPIfNonMatch so IP matching can be attempted after domain rules do not match.

## Build and download
GitHub Actions runs on push, manually, and daily. It uploads all files under dist/ as a workflow artifact and publishes the binary GeoSite plus route fragment to the latest release. The repository is private, so the release is not anonymously accessible. Download the asset while signed in to GitHub, then import custom.dat into Streisand's Geofiles before using the ext:custom.dat tags.

## Sources
The source URLs are listed in sources.json and mirror the current upstream RULE-SET dependencies in dlisin's shadowrocket.conf. No RU Universal lists or unrelated lists are added.
