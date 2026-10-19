#!/usr/bin/env python3
"""
Second Shift - DEADFACE CTF

relay-heartbeat.json  = plaintext
relay-heartbeat.enc   = same message encrypted by the relay
relay-tasking.enc     = second message, ciphertext only

CTR mode reuses the counter/nonce, so the keystream is identical for
both messages.  XOR the known plaintext with its ciphertext to recover
the keystream, then XOR that into the target ciphertext.
"""
import binascii

pt_known = open("relay-heartbeat.json", "rb").read()
ct_known = open("relay-heartbeat.enc", "rb").read()
ct_target = open("relay-tasking.enc", "rb").read()

# keystream = known plaintext XOR known ciphertext
keystream = bytes(p ^ c for p, c in zip(pt_known, ct_known))

# recover the target plaintext with the SAME keystream
recovered = bytes(c ^ k for c, k in zip(ct_target, keystream))

print(recovered.decode("utf-8", "replace"))

# -> flag: deadface{ctr_nonce_reuse_breaks_confidentiality}
