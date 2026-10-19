# Writeup — You Wouldn't Git It

| | |
|---|---|
| **Category** | OSINT + Web |
| **Author** | @Cyb0rgSw0rd |
| **Points** | 125 |
| **Source** | https://doomscroll.dctf.io/ |
| **Flag** | `deadface{13_h4ck3r5_walk3d_int0_a_bar_each_says_Ill_h4v3_a_r00t_b33r}` |

A direct continuation of **The Vibes Are Freaking Me Out**. The intended artifacts are the
GhostTown forum and the `fr34ked0ut/HIPS` repo — the *"Cyb0rg's Unicode Steganography Kit"*
browser extension. That extension's codec table is literally the answer key: every payload
below is one of its named schemes (**Space Variants**, **Zero‑Width**, **TAG block**).

---

## 1. Scope: the target isn't on `deadface.io`

The most important line in the whole event is in the CTF briefing:

> *"Every in-scope target lives on a subdomain of **dctf.io**. You'll also find **deadface.io**
> subdomains, like GhostTown, that hold useful information. Browse them for clues, but
> **never scan or attack them. They're for information only.**"*

So the OSINT lives on `deadface.io` (GhostTown + the HIPS repo) and the **web target lives on
`dctf.io`**. (Chasing `ghosttown.deadface.io/api/v1/` is a trap — it always answers
`401 Invalid or revoked token`.)

The hint thread is GhostTown **Tech Talk → ["Who knew doomscrolling could be so useful?"](https://ghosttown.deadface.io/t/59/who-knew-doomscrolling-could-be-so-useful)**.
The characters describe a "**DoomScroll**" app whose API lets them "communicate without
actually putting anything in the posts people see", and `mirveal` lists candidate paths:

```
/api/posts/<id>/comments
/api/users/<id>/notes
/api/posts/<id>/meta
/api/feed/<id>/details
/api/posts/<id>/history
```

## 2. Finding the app

Brute-force `*.dctf.io` against a short wordlist (app names, service names, the character
handles):

```python
for w in ["doomscroll","dmf","admin","api","app","charon","social","feed", ...]:
    resolve(w + ".dctf.io")
```

```
doomscroll.dctf.io -> 161.35.124.66      <-- the target
dmf.dctf.io        -> 137.184.33.18
admin.dctf.io      -> 64.225.115.250
```

`https://doomscroll.dctf.io/` is a small Flask social network — *"DoomScroll — Social media
for the digital underworld"*.

## 3. The API leaks what the page hides

Nothing on the site requires auth, and the JSON API mirrors the UI — **plus fields the UI
never renders**:

```
GET /api/posts                  -> paged list of posts (?limit=&offset=)
GET /api/posts/<id>             -> one post
GET /api/posts/<id>/comments    -> comments
GET /api/posts/<id>/meta        -> key/value metadata   <-- not shown in the UI
GET /api/users                  -> user list
GET /api/users/<username>       -> profile (bio, website, id)
```

Walking every post id and dumping its `meta` yields the covert channel. Only eight meta rows
exist, all on posts `200, 223, 224, 226, 227, 228, 235`:

| post | key | note |
|---|---|---|
| 200 | `filename` | `travis_001.png` (plain decoy) |
| 200 | `what whaaaaat` | space‑variant payload |
| 223–228 | `pt1`…`pt5` | the message, split in five |
| 235 | `passcode` | space‑variant payload |

## 4. Decoding the meta — Space Variants (base‑3)

Every encoded value is built from exactly three **space** code points, invisible in a browser:

* `U+2002` EN SPACE → `0`
* `U+2003` EM SPACE → `1`
* `U+2009` THIN SPACE → `2`

This is the HIPS extension's *Space Variants* codec ("Encodes bits by choosing between
characters that all render as a gap"). Its "eight space table" preset encodes **3 bits per
character**; the author used a ternary variant. The tell is the **length**: every value is
divisible by **6**, and 3⁶ = 729 ≥ 256, so **six trits = one byte**, big‑endian:

```python
value = d0·3**5 + d1·3**4 + d2·3**3 + d3·3**2 + d4·3 + d5
```

```js
const D = { "\u2002":0, "\u2003":1, "\u2009":2 };
const bytes = [];
for (let i = 0; i + 6 <= seq.length; i += 6) {
  let v = 0;
  for (const ch of seq.slice(i, i + 6)) v = v * 3 + D[ch];
  bytes.push(v);
}
const text = bytes.map(b => String.fromCharCode(b)).join("");
```

Decoded:

```
post 200 "what whaaaaat" -> "Check it out, we can use DoomScroll for covert comms"
post 223 "pt1" -> "TGRI's CFO, Santos Staudenmaier, has my attention. ..."
post 224 "pt2" -> "Ooh, following the money? I like it. ;) ..."
post 226 "pt3" -> "Precisely. His financial records could expose TGRI's ..."
post 227 "pt4" -> "Already on it. Santos seems pretty protective of his reputation. ..."
post 228 "pt5" -> "Do not act prematurely. We need evidence before making our move. ..."
post 235 "passcode" -> "https://pastebin.com/GBcnwhvZ"
```

## 5. The dead drop (flavor, not required for the flag)

The `passcode` points at a Pastebin titled **"Cookie Recipe"** containing:

```
KKq5/Gq6qHW4isNitU8wR02wW/+6y+rH7bZODH0Mnc0=
```

```
DEADFACE CTF 2026
```

A 32‑byte base64 blob — extra campaign color / a hook for a sibling challenge, not needed to
get the flag.

## 6. Zero‑width jokes

The HIPS *zero‑width* codec (`U+200B` = 0, `U+200C` = 1, 8 bits/char) hides one‑liners woven
through captions and comments:

| Location | Decoded |
|---|---|
| post 239 caption (`gh0st404`) | *"id tell u a TCP joke but id have to keep resending it until u acknowlege it"* |
| post 246 caption (`sunstalker`) | *"Was chasing a hacker but he got away. I think he ransomware."* |
| post 247 comment (`sunstalker`) | *"Why do hackers love dark mode? Because light attracts bugs."* |
| post 247 comment (`lilith`) | *"Why did the hacker fail math? He only knew how to count"* |
| post 247 comment (`lilith`) | *"Yes, we're using it... it's actually pretty cool!"* |
| post 210 comment (`lamia415`) | *"drinks later?"* |

> `U+FE0F` (emoji variation selectors) also shows up all over — that's just emoji, not a payload.

## 7. The flag — TAG block

One comment on **post 247 by `b1tfr34k`** (comment id `496`) dresses as gibberish
(*"GREEN GIRAFFES CHOCOLATE LEPERS LEAPING…"*) but carries **TAG characters**
(`U+E0000`–`U+E007F`). Subtract `0xE0000` and you get ASCII directly — the HIPS *tag‑block*
codec:

```js
let out = "";
for (const ch of body) {
  const cp = ch.codePointAt(0);
  if (cp >= 0xE0000 && cp <= 0xE007F) out += String.fromCharCode(cp - 0xE0000);
}
```

```
YES! YOU'RE ALL USING IT! deadface{13_h4ck3r5_walk3d_int0_a_bar_each_says_Ill_h4v3_a_r00t_b33r}
```

---

## Summary

| Step | Technique | Result |
|---|---|---|
| 1 | Read the scope statement | in‑scope targets are `*.dctf.io` |
| 2 | GhostTown topic 59 + `*.dctf.io` wordlist | `doomscroll.dctf.io` |
| 3 | Unauthenticated `/api/posts/<id>/meta` dump | 8 hidden meta rows |
| 4 | Space Variants base‑3 decode (U+2002/2003/2009) | covert comms + Pastebin URL |
| 5 | Scan captions/comments for invisible Unicode | zero‑width jokes |
| 6 | TAG‑block decode (U+E0000 − 0xE0000) | **`deadface{13_h4ck3r5_walk3d_int0_a_bar_each_says_Ill_h4v3_a_r00t_b33r}`** |

## Takeaways

* **Read the scope rules first.** Everything on `deadface.io` is a honeypot for this task —
  including a *convincing* `401` API that will eat your afternoon. The real app was one DNS
  lookup away on `dctf.io`.
* **Diff the API against the page.** Fields the UI never renders (`meta`, unrendered
  comment bodies) are the standard covert-comms channel. If a value exists in JSON but not on
  screen, that's the challenge.
* **Space characters are a stego channel.** `U+2002/2003/2009` look identical in a browser but
  are distinct bytes in JSON. Length divisibility (÷6 here) is the fingerprint of a base‑N
  encoding.
* **TAG characters ride inside normal text.** `U+E0000`–`U+E007F` render as *nothing* after any
  glyph, so a comment can read as pure nonsense while carrying a full ASCII payload.
* **The "artifact" is the cheat sheet.** The HIPS extension from the previous challenge
  documents every scheme by name and parameters — read its codec table and each hidden blob
  becomes a lookup, not a guess.

## Tools Used

- `socket`/`getaddrinfo` for the `*.dctf.io` subdomain sweep
- `fetch` + regex to pull posts, comments and meta from the DoomScroll JSON API
- Custom JS/Python decoders for base‑3 (Space Variants), bit‑pair (zero‑width) and `−0xE0000`
  (TAG block)
- The `fr34ked0ut/HIPS` source (`dist/src/popup/popup.js`) as the codec reference
