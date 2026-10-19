# Infrequent Emojis

**Category:** Cryptography
**Points:** 50
**Challenge:** DoomScrolling
**Author:** @Cyan
**Target:** <https://doomscroll.dctf.io/>

## Flag

```text
deadface{please_try_out_my_new_standard}
```

## Reconnaissance

The challenge is hosted as a social-media-style site called DoomScroll. Guest
users can browse the feed without logging in. Paginating through the feed
reveals a suspicious post:

- **Post:** 252
- **User:** `spookyboi`
- **URL:** <https://doomscroll.dctf.io/post/252>

The post caption and comments contain many unusual emojis instead of ordinary
text. The attached image is also made from the same emoji alphabet.

## The clue in the comments

The first encoded caption can be solved as a monoalphabetic substitution. It
decodes to:

```text
the lookup table is live. all active communications must shift to this format to bypass standard string scanners.
```

This confirms that the emojis are being used as a symbol-for-letter lookup
table rather than as a conventional emoji puzzle.

Several comments provide additional plaintext and make it possible to fill in
the remaining symbols. For example:

```text
re🔌ects ra🔥
```

becomes:

```text
rejects raw
```

## Emoji lookup table

| Emoji | Letter | Emoji | Letter | Emoji | Letter |
|---|---:|---|---:|---|---:|
| ☣️ | t | 💾 | h | 🕯️ | e |
| 🕸️ | l | 🖤 | o | 📡 | k |
| 🌩️ | u | 🦉 | p | 💀 | a |
| ☠️ | b | 📟 | i | 🌙 | s |
| ☢️ | v | ⚰️ | c | ⛓️ | m |
| 🦇 | n | 🩸 | f | 🔮 | r |
| 🧪 | y | 🪦 | d | 🦴 | g |
| 🔌 | j | 🔥 | w | 🔏 | z |
| 🥀 | x | 👁️ | q | | |

## Decode the image

The source image for the challenge is included in this directory:

![Infrequent Emojis challenge image](./infrequent-emojis.png)

Reading the symbols from left to right and applying the lookup table gives:

```text
deadface{please_try_out_my_new_standard}
```

The result matches the required `deadface{...}` submission format.

## Files

```text
README.md
infrequent-emojis.png
```
