# Data Go Brrrrr — Writeup

**Challenge:** RP-01? pcap
**Category:** Network / Forensics
**Flag:** `deadface{icmp_3xfil_wh3n_th3y_least_susp3ct}`

## Scenario

The client reports data leaving their network from a small segment of
traffic. We are given a small PCAP (`PCAP01.pcap`, 34 packets) and asked
to find the exfiltrated data.

## Analysis

### 1. Get an overview of the capture

Opening the PCAP (e.g. `tshark -r PCAP01.pcap` or Scapy's `summary()`)
shows only three kinds of traffic:

| # | Traffic | Notes |
|---|---------|-------|
| 8 | ICMP echo request/reply `192.168.1.50` ↔ `192.168.1.1` | Local gateway pings — payload is a static 64-byte ramp `\x08\x09...7`. Noise. |
| 1  | DNS query/response `www.example.com` → `93.184.216.34` | Lead-in / decoy. |
| 1  | TCP HTTP `192.168.1.50:44001` → `93.184.216.34:80` | Small push/pull — decoy. |
| 16 | ICMP echo request/reply `192.168.1.50` ↔ `10.10.14.7` | **The interesting part.** Requests carry data; replies are just `OK`. |

The standout is the ICMP chatter with `10.10.14.7` — an internal address
that should never see this volume of ping traffic.

### 2. Extract the echo-request payloads

Filtering for ICMP echo requests (type 8) to `10.10.14.7` and dumping
the raw payload of each gives:

```
ZGVhZGZh
Y2V7aWNt
cF8zeGZp
bF93aDNu
X3RoM3lf
bGVhc3Rf
c3VzcPNj
dH0=
```

These are clearly **base64** chunks of a single message.

### 3. Reassemble and decode

Concatenate the chunks in wire order and base64-decode:

```
ZGVhZGZhY2V7aWNtcF8zeGZpbF93aDNuX3RoM3lfbGVhc3Rfc3VzcDNjdH0=
    ↓ base64 -d
deadface{icmp_3xfil_wh3n_th3y_least_susp3ct}
```

## Technique

**ICMP exfiltration** — a compromised host smuggles data inside the
data portion of ICMP echo-request packets. Ping traffic is usually
allowed through firewalls and rarely inspected, and the chunks are
base64-encoded so the payloads survive any ASCII-only intermediary.
The receiving side acknowledges each chunk with a short `OK` echo
reply, making it look like a (very chatty) keepalive.

## Detection / IOCs

- Host `192.168.1.50` pings internal address `10.10.14.7` repeatedly
  with non-standard, base64-looking payloads (normal pings carry
  repeating byte ramps).
- Replies from `10.10.14.7` are only 2 bytes (`OK`) — asymmetric
  payload sizes are the tell.

## Reproduction

`python solve.py` (in this folder) reads `PCAP01.pcap`, pulls the
echo-request payloads destined to `10.10.14.7`, and decodes them.

## Lessons

- Treat unexpected ICMP flows — especially internal-to-internal —
  with suspicion; ping is a tunnel, not just a liveness check.
- Normal echo payloads are repetitive ramps; high-entropy or
  base64-looking ping data is anomalous.
- Firewall egress rules that "allow ping" need payload inspection,
  not just protocol allowance.
