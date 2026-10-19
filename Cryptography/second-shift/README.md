# Second Shift

**Category:** Crypto
**Provided:** `relay-heartbeat.json`, `relay-heartbeat.enc`, `relay-tasking.enc`

## Analysis

The relay preserved one transmission *before* and *after* processing:

- `relay-heartbeat.json` – the plaintext heartbeat message (251 bytes, incl. trailing `\n`)
- `relay-heartbeat.enc` – the same message encrypted (250 bytes)

A second outbound transmission, `relay-tasking.enc`, exists only as ciphertext.

Encrypting the identical 250-byte prefix twice yields two ciphertexts and gives us a
classic **keystream reuse** (CTR nonce/counter reuse) situation. In a stream cipher the
ciphertext is `C = P XOR keystream`. With a known plaintext pair we recover the keystream:

```
keystream = PT_known XOR CT_known
```

Applying that same keystream to the target ciphertext recovers the tasking message.

## Solve

```python
keystream = bytes(p ^ c for p, c in zip(open("relay-heartbeat.json","rb").read(),
                                       open("relay-heartbeat.enc","rb").read()))
print(bytes(c ^ k for c, k in zip(open("relay-tasking.enc","rb").read(), keystream)).decode())
```

## Recovered tasking

```json
{"type":"tasking","target":"aurora-vpn","action":"stage-access","window":"00:30Z","operator":"mort1cia","note":"Use the backup tunnel. Archive bundle under DEADFACE{ctr_nonce_reuse_breaks_confidentiality} before exfil."}
```

DEADFACE was preparing to **stage access to `aurora-vpn`** at `00:30Z` through a backup tunnel.

## Flag

```
deadface{ctr_nonce_reuse_breaks_confidentiality}
```
