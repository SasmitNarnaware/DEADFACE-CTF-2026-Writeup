import base64
from scapy.all import rdpcap, ICMP, IP, Raw

pkts = rdpcap("PCAP01.pcap")

# Exfil channel: ICMP echo-request payloads from 192.168.1.50 -> 10.10.14.7
# (Replies from the local gateway 192.168.1.1 are just noise; the
#  10.10.14.7 replies are only b"OK" acknowledgements.)
chunks = []
for p in pkts:
    if ICMP in p and Raw in p and p[ICMP].type == 8:
        if p[IP].dst == "10.10.14.7":
            chunks.append(bytes(p[Raw].load).decode())

b64 = "".join(chunks)
print("Exfiltrated stream:", b64)
print("Flag:", base64.b64decode(b64).decode())
