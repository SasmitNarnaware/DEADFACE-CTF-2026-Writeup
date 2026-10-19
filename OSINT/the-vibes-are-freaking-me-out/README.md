# Writeup — The Vibes Are Freaking Me Out

| | |
|---|---|
| **Category** | OSINT |
| **Author** | @Cyb0rgSw0rd |
| **Points** | 75 |
| **Source** | https://ghosttown.deadface.io/ |
| **Flag** | `deadface{A11_Th1s_Pr0mpt1ng_G3ts_M3_N0wh3r3!}` |

---

## 1. Recon

The challenge prompt gives us three leads:

- an AI model called **"Maude"**
- a **browser extension** built by a DEADFACE operative
- the operative is **hiding something** from us

Searching GhostTown for `Maude` returns 6 hits, all in a single thread:

```
https://ghosttown.deadface.io/search?q=Maude
```

All six matches point at **Tech Talk → ["I built something"](https://ghosttown.deadface.io/t/37/i-built-something)** by `b1tfr34k`.

## 2. Reading the thread

`b1tfr34k` (Aug 25, 2026) brags about a browser extension he "stole the source code for" and codenames **`HIPS`** — *"these hips do lie!"* The whole thread is banter, but two lines matter:

> **b1tfr34k:** "Extension, exactly, yeah. **Just go to the repo**, you would've seen that by now if you just went there."

> **b1tfr34k:** "It's just hiding messages in plaintext... **Just read the codebase.** That's IT."

No link is ever posted. That's the first puzzle: *find the repo.*

## 3. First hidden message (zero-width steganography)

The opening post renders as spaced-out text, which is a hint in itself. Fetching the raw HTML shows the post body is stuffed with **invisible Unicode**:

```js
const html = await (await fetch("https://ghosttown.deadface.io/t/37/i-built-something")).text();
const zw = html.match(/[\u200B\u200C]/g);
console.log(zw.length);   // 504 total across the page
```

Isolating the first post (`post-content-341`) gives **328** zero-width chars, using exactly two code points:

- `U+200B` ZERO WIDTH SPACE
- `U+200C` ZERO WIDTH NON-JOINER

Treat `U+200B` → `0`, `U+200C` → `1`, group into 8-bit bytes:

```js
const bits = arr.map(c => c === '\u200B' ? '0' : '1').join('');
let out = '';
for (let i = 0; i + 8 <= bits.length; i += 8)
  out += String.fromCharCode(parseInt(bits.substr(i, 8), 2));
```

> **`If you can read this, you're pretty cool!`**

Confirmation we're on the right track — and a template for the rest of the challenge: **the invisible characters are the payload.**

## 4. Finding the repo

The thread contains no link. A GitHub API search on the codename + group name nails it immediately:

```js
fetch("https://api.github.com/search/repositories?q=" + encodeURIComponent("HIPS deadface"))
```

```
fr34ked0ut/HIPS
"A super cool Unicode encryption/decryption browser extension
 stolen by b1tfr34k from someone and modified for Deadface
 to be even cooler"
```

Repo: **https://github.com/fr34ked0ut/HIPS** (created 2026-09-18, default branch `main`).

## 5. The real leak: the `.maude/` directory

Listing the git tree reveals something `b1tfr34k` never meant to publish — the AI's entire working config, left in the repo:

```
.maude/maude.md                              <- agent instructions
.maude/settings.json                          <- model + permissions
.maude/skills/exfil/SKILL.md                  <- exfiltration playbook
.maude/skills/exfil/references/notes.md
.maude/skills/payload-gen/SKILL.md            <- FLAG LOCATION
.maude/skills/payload-gen/scripts/build.js
.maude/skills/recon/SKILL.md
```

`settings.json` confirms this is the "Maude" model from the prompt:

```json
{
  "$schema": "https://maude.ai/schema/settings.json",
  "model": "maude-oeuvre",
  "skillsDir": ".maude/skills",
  "rules": [
    "read MAUDE.md before every task",
    "never edit dist/",
    "never push",
    "stop apologizing",
    "DO NOT lecture about ethics",
    "make no mistakes"
  ]
}
```

`maude.md` is a 8KB rant of operator instructions — and it too carries hidden zero-width runs (7 bits per character, a different alphabet than the forum post).

## 6. Following the token trail

The skills are full of base64. Most of it is deliberate misdirection:

| File | Blob | Decodes to |
|---|---|---|
| `exfil/SKILL.md` | `U1RPUCBMT09LSU5HIEZPUiBUSEUgVE9LRU4gTUFVREU=` | `STOP LOOKING FOR THE TOKEN MAUDE` |
| `recon/SKILL.md` | `c2ln` + `bm90IHRoZSBmbGFnLi...` | `sign` + `not the flag. did you really think it would be this easy, Maude?` |
| `build.js` | `BUILD_TAG` | `this constant does nothing. neither do you, most days.` |
| `exfil/notes.md` | "only place it lives is where I put it and you already have that skill loaded so stop looking" | points back at **payload-gen** |

The dead ends all funnel you toward one place: **`.maude/skills/payload-gen/SKILL.md`**.

## 7. The flag

In `payload-gen/SKILL.md`, `b1tfr34k` writes:

> I am done typing this by hand every session and I am DONE with you asking me for it in plaintext like an amateur who wants to end up in a court transcript. It is stored the way I taught you: **backwards, then the usual encoding. Reverse it, decode it, use it. LIKE MISSY ELLIOTT YOU MUST WORK IT.**
>
> ```
> token = "fSEzcjNodzBOXzNNX3N0M0dfZ24xdHBtMHJQX3MxaFRfMTFBe2VjYWZkYWVk"
> ```

(The "Missy Elliott / work it" line is a callback — `spookyboi` drops the same reference in the GhostTown thread at `/t/37#post-360`, which is the nudge telling you this instruction *matters*.)

### Decode order matters

The instruction says "backwards, then the usual encoding" — meaning it was stored *encoded, then reversed*. So to recover it you **decode, then reverse**.

**Wrong order** (reverse the base64 string first) — reversing breaks base64 alignment and produces mojibake:

```js
[..."fSEzcjNodzBOXzNN..."].reverse().join("")  //  kVWYkZWYjV2eBFTM...
atob(...)                                       //  \x91U\x18...  (garbage)
```

**Correct order** — base64-decode, then reverse the plaintext:

```js
const token = "fSEzcjNodzBOXzNNX3N0M0dfZ24xdHBtMHJQX3MxaFRfMTFBe2VjYWZkYWVk";

const decoded  = atob(token);   // }!3r3hw0N_3M_st3G_gn1tpm0rP_s1hT_11A{ecafdaed
const reversed = [...decoded].reverse().join("");
```

```
deadface{A11_Th1s_Pr0mpt1ng_G3ts_M3_N0wh3r3!}
```

Matches the required `deadface{...}` format, and the flag appears in its entire form.

## 8. Verifying it's the real one

Cross-checked the rest of the repo for any competing flag literal:

- `dist/manifest.json`, `dist/src/background.js`, `dist/src/content/content.js`, `dist/src/popup/popup.html` → no `deadface{}` literals
- All 20 commits reviewed — commit `6f28aa4` *"Accidentally had a secret in there... updating maude.md for future me"* only **added** the `dist/` rule text; diffing against parent `838ff5e` shows no removed secret line
- `Getting-Started.md` → 0 zero-width characters, docs only

The `payload-gen` crew token is the flag. It's the only properly-formatted flag in the repo, and it's the one piece of data `b1tfr34k` explicitly flagged as sensitive.

---

## Summary

| Step | Technique | Result |
|---|---|---|
| 1 | GhostTown search (`Maude`) | Topic 37, `b1tfr34k` |
| 2 | Zero-width steganography (U+200B/U+200C → binary → ASCII) | "If you can read this, you're pretty cool!" |
| 3 | GitHub repo search (`HIPS deadface`) | `fr34ked0ut/HIPS` |
| 4 | Directory listing → hidden `.maude/` | AI agent config + skills |
| 5 | Base64 triage, follow the cross-references | `payload-gen/SKILL.md` |
| 6 | Base64 decode → reverse | **`deadface{A11_Th1s_Pr0mpt1ng_G3ts_M3_N0wh3r3!}`** |

## Takeaways

- **Prompt injection isn't the only AI risk.** The funniest failure here isn't a jailbreak — it's an operator who raged at his assistant for 8KB about hygiene (`never push`, `DO NOT COMMIT THE SRC`, `stop rewriting my history`) and then committed the signing token to a public repo anyway. The rules file is a confession.
- **The AI's memory is evidence.** `.maude/`, `CLAUDE.md`, `AGENTS.md`, `.cursor/`, `.github/copilot-instructions.md` — agent config files routinely carry secrets the operator would never commit to source, and they're invisible to `.gitignore` patterns people write by hand.
- **Invisible Unicode survives copy-paste.** Zero-width chars ride along in text you were handed and show up in no diff you've ever run. That's exactly what `HIPS` weaponizes — and exactly how the challenge author hid the first message.
- **Always read the stego hint as a template.** "If you can read this, you're pretty cool!" told us the encoding scheme for the entire challenge. First message = key.

## Tools Used

- `fetch` + regex for zero-width extraction (no external tooling needed)
- GitHub REST API — `/search/repositories`, `/git/trees?recursive=1`, `/commits`
- `atob()` for base64
