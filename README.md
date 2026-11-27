# Streisand rules based on dlisin/shadowrocket-config

This repository builds an Xray GeoSite database and an importable Streisand routing profile from the rule sources referenced by the current upstream dlisin shadowrocket.conf.

## Build outputs

- `custom.dat`: Xray GeoSite database with `DIRECT` and `PROXY` domain categories.
- `custom-geoip.dat`: separate Xray GeoIP database with `DIRECT` and `PROXY` IP categories.
- `custom-combined.dat`: experimental single-file hybrid containing both domain and IP entries under distinct tags.
- `streisand-route.txt`: standard two-file import link in Streisand's `streisand://import/route://` binary-plist format.
- `streisand-route-combined.txt`: experimental import link using only `custom-combined.dat`.
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

## Experimental single-file option

Xray's external geodata lookup scans the shared protobuf entry envelope by category tag. GeoSite and GeoIP entries can therefore be placed in one hybrid file if every category has a unique tag. The experimental `custom-combined.dat` uses `DIRECT-DOMAIN`, `PROXY-DOMAIN`, `DIRECT-IP`, and `PROXY-IP`. Its route profile references those four tags in the same file.

This is not a standard standalone GeoSite or GeoIP database. It relies on Xray's tag-based external-file loader accepting both entry types in one file. CI checks the protobuf records and the generated import link, but only an actual Streisand runtime test can confirm compatibility with the installed app/core version. Keep using the standard two-file profile unless the combined profile passes that device test.

## Installation

1. Standard, verified layout: add both `custom.dat` and `custom-geoip.dat` to Streisand's Geofiles, then import `streisand-route.txt`.
2. Single-file experiment: add only `custom-combined.dat`, then import `streisand-route-combined.txt`. Do not switch to this option until it has been tested on the target Streisand version.
3. Enable the selected routing profile.

Alternatively, use `streisand-route-standalone.txt` if you do not want to configure a GeoFile. This profile embeds the current domain rules. It must be re-imported after a new release to receive updated domain lists. The GeoFile-based profile remains the smaller and easier-to-refresh option.

The generated import profile uses the existing `direct` and `proxy` outbound tags. It does not change VLESS/Reality nodes.

The repository is public. Stable direct URLs for the standard Geofiles are `https://github.com/kraftmikila/streisand-dlisin/releases/latest/download/custom.dat` and `https://github.com/kraftmikila/streisand-dlisin/releases/latest/download/custom-geoip.dat`. The experimental single-file URL is `https://github.com/kraftmikila/streisand-dlisin/releases/latest/download/custom-combined.dat`. These URLs point to assets attached to the latest successful release.

## Updates and validation

GitHub Actions rebuilds on push and daily. It validates the GeoSite protobuf categories and decodes the generated Streisand binary-plist import payload before publishing. Successful builds publish the files as a workflow artifact and release assets.

## Sources

The exact source URLs are listed in `sources.json`. They mirror the RULE-SET dependencies referenced by the upstream dlisin config. No RU Universal or unrelated lists are added.
