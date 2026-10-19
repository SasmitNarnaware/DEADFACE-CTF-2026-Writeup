# Spooky Cereals — The Nordics (re03) Writeup

## Challenge
The Nordics (Viking/LotR-Elf-looking aliens) told us, via a Lytton Labs device, their favorite terrestrial breakfast cereal. We need to reverse the provided Linux/Windows challenge binaries to find the flag.

Format: `deadface{...}` — no spaces, periods, or asterisks.

## Files
Encrypted archive: `re03-ck02.7z` (128 KB)
- SHA256: `e4742efa2cb7c45353d7f87f4427f9abe3b450eea5469732e7b790647017c7ac`
- Password: `KlippyAI`

Extracted contents:
| File | Type |
|------|------|
| `re03-lin-x86.bin` | Linux ELF challenge binary (analyzed) |
| `re03-win-x86.exe` | Windows challenge binary |
| `KlippyAI-trained-on-CK02.exe` | Bonus/surprise program — **do not run on host** |

## Recon
- ELF is **not stripped** (`re03.c` source name present).
- `main` at `0x133b`, size 1249 bytes.
- Imports used: `memcpy`, `memset`, `memcmp`, `memmem`, `putchar`, `puts`.
- `.rodata` at `0x2000` contains:
  - A 256-byte ciphertext at `0x2A20`
  - A 256-byte embedded key at `0x2B24`
  - In-story strings plus box-drawing frame text

## Algorithm (`main`)
1. Copy 0x101 bytes into a stack buffer.
2. Copy 0x100 bytes into a second stack buffer.
3. XOR loop (0x100 iterations): `out[i] = cipher[i] ^ key[i]` → `out` at `ebp-0x11d`.
4. `memmem(out, 0x100, "badff00d", 7)` — checks if the *tampered* needle `"badff00d"` (double `f`) appears in output.
5. If found → error path ("key has been tampered with").
6. If not found → `puts(out)` prints the flag.

## The Catch
The embedded key has been tampered with. The story hint gives the fix:

> "TIME is REVERSIBLE, but the KEY is NOT... Go Back!"

Interpretation: reverse the ciphertext ("time"/order is reversible), but do **not** reverse the key. Equivalently, XOR the ciphertext with the **reversed** embedded key.

## Decryption
```
ct     = data[0x2A20 : 0x2B20]   # 256 bytes ciphertext
key    = data[0x2B24 : 0x2C24]   # 256 bytes embedded (tampered) key
plain  = ct[i] ^ key[255 - i]    # reverse key, not ciphertext
```

Resulting plaintext box (punctuation/padding stripped):

```
feed . . .
face . . .
dead beef
dead . . .
face {
N0rdics
-R3ally-like-
Frank3nb3rry-
cuz-bro-is-
tall-like-
they-are!
badf00d......
d a 7e4107
```

Reading the message lines in order, removing the frame borders:

`deadface{N0rdics-R3ally-like-Frank3nb3rry-cuz-bro-is-tall-like-they-are!}`

The `"badf00d"` (single f) that appears in the box is intentionally **not** the `memmem` needle `"badff00d"` (double f), so the check passes and the flag is printed.

## Flag
```
deadface{N0rdics-R3ally-like-Frank3nb3rry-cuz-bro-is-tall-like-they-are!}
```

## Notes
- The Windows binary (`re03-win-x86.exe`) contains the same logic; an `objdump` of it was also captured during analysis.
- Do NOT run `KlippyAI-trained-on-CK02.exe` on a host machine — run it only in a VM (it is packed and flagged as a "surprise").
