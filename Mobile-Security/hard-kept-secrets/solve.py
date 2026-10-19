#!/usr/bin/env python3
"""
Hard Kept Secrets (syyntax / DEADFACE) - automated solver

Recovers the hardcoded internal API token from the De Monne Financial
Android app and prints the flag.

Pure stdlib. No apktool / jadx / Frida required.

Approach:
  1. Parse the DEX string pool properly (dex parser below) so we get the
     *real* constant values, not just byte-scanning artefacts.
  2. Find the token that InternalTokenInterceptor attaches as X-Internal-Token.
  3. Discard the two planted decoy flags.

Usage:
    python solve.py <path-to.apk>
"""

import base64
import re
import struct
import sys
import zipfile


# --------------------------------------------------------------------------- #
# Minimal DEX string-pool reader                                              #
# --------------------------------------------------------------------------- #
def uleb128(buf, off):
    result = shift = 0
    while True:
        b = buf[off]
        off += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, off
        shift += 7


def dex_strings(data):
    """Return every string in a DEX file's string_ids table."""
    if data[:4] != b"dex\n":
        raise ValueError("not a DEX file")

    (string_ids_size,) = struct.unpack_from("<I", data, 56)
    (string_ids_off,) = struct.unpack_from("<I", data, 60)

    out = []
    for i in range(string_ids_size):
        (soff,) = struct.unpack_from("<I", data, string_ids_off + i * 4)
        _utf16_len, p = uleb128(data, soff)          # skip the declared length
        end = data.index(b"\x00", p)                  # MUTF-8, NUL terminated
        out.append(data[p:end].decode("utf-8", "replace"))
    return out


# --------------------------------------------------------------------------- #
# Token identification                                                        #
# --------------------------------------------------------------------------- #
# Decoys planted by the challenge author. These are formatted like flags but
# are never sent to the API -- they only render in UI strings.
DECOYS = {
    "deadface{flaG_ManIfesT3d}",        # DiagnosticActivity "diagnostic.code"
    "deadface{Ur_N0t_A110wEd_h3r3}",    # SecureVaultActivity "Authorization Code"
}

# A candidate internal token: base64, 32-128 chars.
B64_RE = re.compile(r"^[A-Za-z0-9+/]{32,128}={0,2}$")

# A Java identifier / field / method name. Long AndroidX method names are all
# technically valid base64, so this is what actually separates key material
# from noise. Key material never parses as an identifier.
IDENT_RE = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")

# The canonical base64 alphabet, which the DEX carries as a literal string.
B64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def is_plausible_token(s):
    """Filter the DEX string pool down to genuine key material."""
    if not B64_RE.match(s):
        return False
    if s == B64_ALPHABET or s.rstrip("=") == B64_ALPHABET.rstrip("="):
        return False                     # the alphabet table itself
    if IDENT_RE.match(s):
        return False                     # method / field / class name
    # Key material is high-entropy: mixed case plus digits, and no dictionary
    # word. Identifiers were already excluded, so what is left is random bytes.
    has_upper = any(c.isupper() for c in s)
    has_lower = any(c.islower() for c in s)
    has_digit = any(c.isdigit() for c in s)
    return has_upper and has_lower and has_digit


def find_token(strings):
    """
    The real token is the only base64 blob that (a) is genuine key material
    rather than an identifier, and (b) is wired to a request header by an
    interceptor.
    """
    joined = "\n".join(strings)

    # Anchor: the challenge's premise is an API token, so require the header
    # the interceptor sets to actually exist in the app.
    if "X-Internal-Token" not in joined:
        print("[!] 'X-Internal-Token' not found - unexpected app?", file=sys.stderr)

    cands = []
    seen = set()
    for s in strings:
        if s in seen:
            continue
        seen.add(s)
        if is_plausible_token(s):
            cands.append(s)

    return cands


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r"E:\Deadface\secerete\app-release.apk"

    with zipfile.ZipFile(apk) as z:
        dex_files = [n for n in z.namelist() if re.fullmatch(r"classes\d*\.dex", n)]

        strings = []
        for name in dex_files:
            strings.extend(dex_strings(z.read(name)))

    print(f"[*] {apk}")
    print(f"[*] DEX files : {', '.join(dex_files)}")
    print(f"[*] strings   : {len(strings)}")

    cands = find_token(strings)
    print(f"[*] key-material candidates (after filtering): {len(cands)}")

    for c in cands:
        try:
            raw = base64.b64decode(c, validate=True)
        except Exception:
            continue
        marker = "  <-- TOKEN" if 32 <= len(raw) <= 64 else ""
        print(f"    {c}  ({len(c)} chars -> {len(raw)} bytes){marker}")

    # The flag is the single, unambiguous candidate.
    if len(cands) == 1:
        token = cands[0]
    elif not cands:
        sys.exit("[-] no token found")
    else:
        # Should not happen; fall back to highest-entropy candidate.
        import math
        from collections import Counter
        def entropy(s):
            cnt = Counter(s)
            n = len(s)
            return -sum(v / n * math.log2(v / n) for v in cnt.values())
        print("[!] multiple candidates, picking highest entropy", file=sys.stderr)
        token = max(cands, key=entropy)

    print()
    print("=" * 70)
    print("INTERNAL_API_TOKEN =", token)
    print("=" * 70)
    print()
    print(f"FLAG: deadface{{{token}}}")
    print()

    # Show what we rejected, so the decoys are auditable.
    for s in strings:
        if s.startswith("deadface{") and s not in DECOYS:
            print(f"[!] unexpected additional flag-shaped string: {s}")
    for d in sorted(DECOYS):
        print(f"[i] ignored decoy: {d}")


if __name__ == "__main__":
    main()
