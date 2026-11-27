# Streisand rules based on dlisin/shadowrocket-config

This repository builds an Xray GeoSite database and an importable Streisand routing profile from the rule sources referenced by the current upstream dlisin shadowrocket.conf.

## Build outputs

- `custom.dat`: Xray GeoSite database with `DIRECT` and `PROXY` domain categories.
- `custom-geoip.dat`: Xray GeoIP database with `DIRECT` and `PROXY` IP categories.
- `streisand-route.txt`: import link in Streisand's `streisand://import/route://` binary-plist format.
- `streisand-route.json`: readable version of the GeoFile-based route profile.
- `streisand-route-standalone.txt` and `.json`: standalone profile with domain rules embedded, no external `custom.dat` required.
- `proxy-ips.txt`, `direct-ips.txt`: readable source lists used to build the GeoIP database.
- `proxy-ports.txt`: destination ports routed through proxy.
- `report.json`: source counts, unsupported rule counts, and download errors.

## Translation

- `DOMAIN-SUFFIX` -> Xray RootDomain.
- `DOMAIN` -> Xray Full.
- `DOMAIN-KEYWORD` -> Xray Regex matching the keyword anywhere in the queried domain.
- `IP-CIDR` and `IP-CIDR6` -> IP route rules.
- Bare IPs in Misha's `domain_ips.list` and zkeen IP release lists -> IP route rules.
- `DST-PORT` -> port route rules. Invisible Unicode characters and en dashes in ranges are normalized.
- `USER-AGENT` and `IP-ASN` cannot be faithfully represented by this Xray GeoSite/IP-CIDR conversion. They are counted as skipped in `report.json`.
- The current upstream `reject.list` is empty, so no reject category is invented.

## Routing order

1. Private/local IP ranges from `ext:custom-geoip.dat:direct` -> DIRECT.
2. `ext:custom.dat:direct` -> DIRECT.
3. `ext:custom.dat:proxy` -> PROXY.
4. Service IP ranges from `ext:custom-geoip.dat:proxy` -> PROXY.
5. Explicit service destination ports -> PROXY.
6. All remaining traffic -> DIRECT.

Each match dimension is a separate rule to avoid accidental AND matching between domain, IP, and port fields. The IP ranges are stored in GeoIP data rather than embedded in the import link, keeping the link compact.

## Installation

1. Add both `custom.dat` and `custom-geoip.dat` to Streisand's Geofiles and wait for them to load.
2. Import `streisand-route.txt` in Streisand using the `+` button in Routing.
3. Enable the imported routing profile.

Alternatively, use `streisand-route-standalone.txt` if you do not want to configure a GeoFile. This profile embeds the current domain rules. It must be re-imported after a new release to receive updated domain lists. The GeoFile-based profile remains the smaller and easier-to-refresh option.

The generated import profile uses the existing `direct` and `proxy` outbound tags. It does not change VLESS/Reality nodes.

The repository is public. Stable direct URLs for Streisand Geofiles are `https://github.com/kraftmikila/streisand-dlisin/releases/latest/download/custom.dat` and `https://github.com/kraftmikila/streisand-dlisin/releases/latest/download/custom-geoip.dat`. Both point to assets attached to the latest successful release.

## Updates and validation

GitHub Actions rebuilds on push and daily. It validates the GeoSite protobuf categories and decodes the generated Streisand binary-plist import payload before publishing. Successful builds publish the files as a workflow artifact and release assets.

## Sources

The exact source URLs are listed in `sources.json`. They mirror the RULE-SET dependencies referenced by the upstream dlisin config. No RU Universal or unrelated lists are added.
