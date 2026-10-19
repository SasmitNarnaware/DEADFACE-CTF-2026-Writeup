# DEADFACE CTF — Cereal Killer 01 (Insectoids) — Writeup

**Category:** Reverse Engineering
**Binary:** `ck1/re01-win-x86.exe`
**SHA-256:** `5D5E9DCCF7179E1D7CAC1DBE2376B8001137D04516CE885A8DBEC4E27231458D`
**Password:** `cookiecrisp`
**Flag:** `deadface{You-Vill-Eat-Ze-Bugz-Und-You-Vill-Be-Happy!!!}`

---

## 0. TL;DR

1. The exe computes `SHA1(password)`, hex-encodes it, and `strcmp`s it against a
   **custom-base64-encoded constant**.
2. `strcmp` is preceded by a custom base64 decoder whose group count is `(len-1)>>2`,
   so the "expected" string pulled out of the binary isn't what it looks like. The only
   reliable way to get the true target hash was to **debug it**.
3. `gdb` at the `strcmp` gave the real expected digest:
   `68158678a3f9d76a3d1ca12d20b2d6af9bd3f290`.
4. Cracking that SHA-1 preimage (themed wordlist) → **`cookiecrisp`**.
5. Entering it makes the program RC4-decrypt a second blob with the password as key,
   yielding a **URL** → `.../unwanted-guests/ick.png`.
6. The PNG literally has the flag printed across the top.

---

## 1. Recon

`re01-win-x86.exe` is a **PE32 (mingw-w64)**, image base `0x400000`, entry `0x401000`.
The story text tells us the "Insectoids" have a favorite terrestrial breakfast cereal and
that we must "get the correct password and obtain the flag."

Tools used:
- `objdump -d` (MinGW) → full disassembly `disasm.txt`
- `strings` → message strings
- A small hand-rolled **PE parser** (Python) to pull bytes out of `.data` / `.rdata`
- **`gdb.exe`** (MinGW) — the decisive tool
- Python (`hashlib`, custom base64 + RC4) to reproduce the crypto

---

## 2. Identifying the pipeline from `main` (`0x4095b0`)

Static analysis of `main` revealed this flow:

```
puts(story)
printf("Please enter the password: ")
getline(&lineptr, &n, stdin)          // narrow bytes, newline stripped
SHA1(digest, lineptr, len)            // 20-byte digest -> stack+0x2f
for each digest byte: sprintf(hex, "%02x", byte)   // 40-char hex -> stack+0x43
strcmp(hex, base64_decode(blob1))     // @ 0x409880
if == 0:
    printf("Access granted")
    base64_decode(blob2) -> buf
    RC4(key=lineptr, data=buf, len, out)   // RC4 with password as key
    fwrite(out)                            // the "flag"
else:
    printf("ACCESS DENIED... HACKER TRACKING ENABLED")
```

Key addresses:

| Thing            | VA        |
|------------------|-----------|
| `main`           | `0x4095b0`|
| `base64_decode`  | `0x401630`|
| `SHA1`           | `0x402b90`|
| `RC4` (`_RC4`)   | `0x402d50`|
| `strcmp`         | `0x408aa8`|
| `"%02x"`         | `0x40b060`|
| custom alphabet  | `0x40b860`|
| blob1 (expected) | `0x40a020`|
| blob2 (enc flag) | `0x40a0a0`|

So the password is checked with **SHA-1**, and the flag is encrypted with **RC4** using
the password itself as the key.

---

## 3. Extracting the constants

A tiny PE parser (parse DOS/PE headers → section table → map `VirtualAddress` to file
offset) pulled the three embedded strings. They're stored as **UTF-16LE**:

**Custom base64 alphabet** (`0x40b860`, 65 chars — a shuffled alphabet, note it contains
`=` and `+`/`/` in odd spots):
```
ZKj9n+yf0wDVX1s/5YbdxSo=ILaUpPBCHg8uvNO4klm6iJGhQ7eFrWczAMEq3RTt2
```

**blob1 — the "expected hash", base64'd** (`0x40a020`, 56 chars):
```
1uH71dHc1FggXcIML9pcId1vXo1gXdwvXuK8XO5cIoIMIO5FLu0MXZ22
```

**blob2 — the encrypted flag, base64'd** (`0x40a0a0`, 80 chars):
```
ZV30LCA0BVSVYYm6jaleC4kNDoqR7su5K70NbkA+voJfAnmUfVLMZhHWjMf=qh5TokdZZdCZx+BdNpA2
```

---

## 4. The custom base64 decoder (and why static analysis lied)

`base64_decode(input, output)` walks the input as **wide chars**, counts them until a
null `WCHAR`, then computes:

```asm
mov  %eax,%ebx      ; ebx = count-1
shr  $0x2,%ebx      ; groups = (count-1) >> 2
...
lea  (%ebp,%ebx,8),%eax   ; end = input + 1 + groups*4 chars
```

So the number of 4-char groups is **`(count-1)>>2`**, *not* `count>>2`. A faithful Python
reproduction of this decoded blob1 to **39 bytes** (`68158678a3f9d76a3d1ca12d20b2d6af9bd3f29`)
and blob2 to 57 bytes — neither a clean multiple that matches a 40-char SHA-1 hex or the
full flag. This produced a genuine contradiction:

> `strcmp` compares a **40-char** hex string against a decoder output that (statically)
> is 39 or 42 bytes. It could never return 0.

I went back and forth on the group arithmetic, the `WCHAR` count, and the stack layout
after `main`'s `rep movsl` copies (which pokes a `'1'` at `stack+0xdc`, extending the
count past 56). None of it reconciled cleanly on paper.

**Resolution: stop guessing, run it.**

---

## 5. Getting the truth with gdb

`gdb` ships with the MinGW toolchain (`C:\mingw32\bin\gdb.exe`). Two gotchas:

1. **Backslashes get mangled** on the command line — use forward slashes in the gdb script.
2. The PE **relocates under ASLR**. `main` was at `0x7e95b5` at runtime (a `0x3e0000`
   delta from `0x4095b5`), so a breakpoint at the static `0x409880` failed with
   *"Cannot insert breakpoint … Cannot access memory."* Fix: `start` to main, compute
   `$base = $pc - 0x4095b5`, then `break *($base + 0x409880)`.

`dbg.gdb`:
```gdb
set confirm off
set pagination off
file E:/Deadface/ck1/re01-win-x86.exe
start < E:/Deadface/input.txt
set $base = $pc - 0x4095b5
break *($base + 0x409880)
continue
set $p = *(unsigned int *)($esp+4)      ; arg2 = base64_decode(blob1)
printf "EXPECTED string = [%s]\n", $p
x/41bx $p
```

Feeding it `test`, gdb showed:
- computed SHA-1 hex (arg1) = `a94a8fe5ccb19ba61c4c0873d391e987982fbbd3`  ← correct `SHA1("test")`
- **expected (arg2) = `68158678a3f9d76a3d1ca12d20b2d6af9bd3f290`**  ← a clean 40-char SHA-1

So despite the decoder weirdness, the runtime expected value **is** a normal 40-char
SHA-1. The static 39/42-byte puzzle was a rabbit hole — memory doesn't lie.

---

## 6. Cracking the SHA-1

Target: `68158678a3f9d76a3d1ca12d20b2d6af9bd3f290`

No online rainbow-table hit. Brute-forcing 1–5 chars wouldn't turn up a real word, so I
built a **themed wordlist** (monster/spooky cereals, every breakfast-cereal brand I could
name, insect/bug terms, and dozens of variants of the story's *"I, for one, welcome our
new … overlords"* line), each expanded through case/spacing/separator permutations
(`lower`, `UPPER`, `Title`, `nospace`, `snake_case`, `kebab-case`, …).

Cracked in ~1s:

```
FOUND: 'cookiecrisp'
```

Note: **`cookiecrisp`** — lowercase, no space. Earlier attempts with `"Cookie Crisp"`
(including a `"CookieCrisp"`/`"cookie crisp"` form) had *failed*; only the fully-flattened
lowercase string matched. That's an easy miss when guessing cereal names by hand.

Verify:
```
SHA1("cookiecrisp") = 68158678a3f9d76a3d1ca12d20b2d6af9bd3f290   ✓
```

---

## 7. Unlocking the flag

Run the binary with the password:

```
Please enter the password: cookiecrisp
Access granted
Good job! You are ALMOST there.. : https://cerealkiller.lyttonlabs.org/unwanted-guests/ick.png
```

The "flag" the program prints is actually **a URL** — the RC4-decrypted contents of blob2
(RC4 key = the password line). So the real flag is behind that link.

> Aside: my from-scratch RC4 reproduced a *slightly* truncated URL
> (`https://cd\x02ealkiller…/ick.p`) because I fed the decoder the buggy `(len-1)>>2`
> length and got 57 bytes instead of the ~60 the binary used. The binary's own output was
> clean, so I just used that.

---

## 8. The image

Downloading `ick.png` (a plain 995×1225 RGBA PNG — no text chunks, no data appended after
`IEND`) and simply **looking at it** reveals the flag printed across the top:

```
deadface{You-Vill-Eat-Ze-Bugz-Und-You-Vill-Be-Happy!!!}
```

with the caption:

> *Dr. Charles K. Gesch-ICK-ter, Director, Lytton Labs*

— a pun emphasizing **"ICK"** (matching the filename `ick.png`, the bug-eating theme, and
the Insectoids). No steganography required; the meme is the payload.

---

## 9. Final answer

```
deadface{You-Vill-Eat-Ze-Bugz-Und-You-Vill-Be-Happy!!!}
```

---

## Lessons / notes

- **When static analysis produces a contradiction, debug.** The custom base64 group-count
  quirk made the expected hash ambiguous on paper; one gdb breakpoint settled it instantly.
- **ASLR relocates the PE** — compute the runtime base (`$pc - static_main`) instead of
  breaking at link-time addresses.
- CTF "passwords" derived from themed nouns are often just the **flattened lowercase**
  form (`cookiecrisp`), which is easy to overlook if you only try the display form.
- The printed "flag" can be a **stepping stone** (here, a URL) rather than the flag itself.
