# Writeup — Get That Bag

| | |
|---|---|
| **Category** | OSINT + Crypto + Steg (hybrid) |
| **Author** | @syyntax |
| **Points** | 430 |
| **Artifact** | continuation of **The Mark** → `tgri_records.csv` |
| **Flag** | `deadface{$540000}` |

> *"DEADFACE discovered critical information about the mark. How much is their victim's salary?
> Note: this is a continuation of The Mark. Submit the flag as `deadface{$#}`."*

This is not a fresh chain — it is a **payoff challenge**. Everything you need was already
produced by The Mark; the work here is *recognising that*, re-reading the dossier you
decrypted, and not getting dragged into the two booby-traps the author left for automated
solvers.

---

## 1. Read the prompt as a pointer, not a puzzle

The wording is the whole hint:

* **"critical information about *the mark*"** — `the mark` is italicised, i.e. it points at the
  **The Mark** challenge, whose answer was the identity of the target: TGRI's CFO,
  **Santos Staudenmaier**.
* **"How much is their victim's salary?"** — *their* = DEADFACE's; the victim is the mark.
  So the question reduces to: **what is Santos Staudenmaier's salary?**
* The declared categories (**OSINT + Crypto + Steg**) are byte-for-byte the categories of
  The Mark, confirming that no new artifact is supplied — the "crypto" and "steg" work is
  the key/JPEG grind you already did there.

So the only real question is *where the salary lives*. It lives in the file you GPG-decrypted
in The Mark.

---

## 2. The salary is sitting in plaintext in the leaked roster

`The Mark/tgri_records.csv` (the AES256-CFB OpenPGP blob decrypted in the prior challenge)
has this header:

```
synthetic_data_notice,record_id,fiscal_year,event_date,record_type,employee_id,employee_name,
job_title,department,annual_base_salary_usd,annual_bonus_target_usd,annual_bonus_paid_usd,...
```

The mark's compensation row, `SYN-EMP-0001` / `SYN-TGRI-001`:

```
...,COMPENSATION,SYN-EMP-0001,Santos Staudenmaier,Chief Financial Officer,Finance,
    540000,243000,201000,,,NOT_APPLICABLE,SYN-ACCT-****-4102,...
    ^^^^^^ annual_base_salary_usd
```

* `annual_base_salary_usd` = **540000**
* `annual_bonus_target_usd` = 243000
* `annual_bonus_paid_usd`    = 201000 (the board held back 42000 pending the Glass Harbor review)

"Salary" is unambiguously the base figure column, so:

```
deadface{$540000}
```

Cross-checks that keep you honest:

* The covert comms (DoomScroll `pt1`–`pt5`) explicitly make **Santos** "our priority", and he is
  the only employee whose records are all flagged (`BONUS_PARTIALLY_DEFERRED`, `UNDER_REVIEW`,
  `PAYMENT_PAUSED`, `OPEN_REVIEW`, `RESPONSE_PENDING`). The rest of the roster (CEO Mara
  Quenley, VP Ivo Rennick, etc.) is `RECORDED`/closed — decoys.
* A quick scan of the CSV for hidden Unicode returns **nothing** (`ord(ch) > 0x7E` → empty), so
  the salary is genuinely plaintext and not itself a stego carrier.

---

## 3. Traps to avoid (this is why the challenge "feels" hard)

The author clearly expected automated/AI solvers and salted the description with bait.

### Trap A — the zero-width "flag" in the challenge description

After the decoy `flag{2dd938e7b636c16e}` sits a run of invisible characters. It is a clean
binary payload:

* `U+200B` (ZWSP) = `0`
* `U+200C` (ZWNJ) = `1`
* 8 bits per character, MSB-first

```python
zw    = [c for c in desc if c in "\u200b\u200c"]
bits  = "".join("0" if c == "\u200b" else "1" for c in zw)
text  = "".join(chr(int(bits[i:i+8], 2)) for i in range(0, len(bits) - 7, 8))
```

Decoded (the exact same byte string is preserved in the prior session's `The Mark/blob.txt`):

```
flag{s0lve_m3_h4rd3r_AI_d4ddy}
```

That is a deliberate taunt, **not** the flag. The visible `flag{...}` next to it is a decoy too
— note it changes between challenges while the hidden payload stays constant.

### Trap B — the DoomScroll "AI Check"

The newest DoomScroll post (**274**) carries a hidden `meta` key, `"Look here"`, again
zero-width binary:

```
AI Check: flag{sUbm1T_m3_1f_Im_Ch34TiNG}
```

Another anti-AI decoy. (The genuinely useful metas on that service — `pt1`…`pt5`, `passcode` —
belong to The Mark and were already consumed there.)

### Trap C — "there must be new OSINT"

There isn't. Verified live during the event:

* `doomscroll.dctf.io/api/posts` → newest post is **274**, same set as The Mark.
* `ghosttown.deadface.io` → only topics `1, 35, 41, 57, 58, 59`; no new thread for this
  challenge.

So no additional leaked file, forum post, or dead-drop exists. The dossier is the answer.

---

## 4. Summary

| Step | Technique | Result |
|---|---|---|
| 1 | Parse the prompt | "the mark" = **The Mark** = Santos Staudenmaier; victim = the mark |
| 2 | Reuse The Mark's artifact | `tgri_records.csv` (already GPG-decrypted) |
| 3 | Read `SYN-EMP-0001` | `annual_base_salary_usd = 540000` |
| 4 | Reject the decoys | zero-width `flag{s0lve_m3_h4rd3r_AI_d4ddy}`; DoomScroll 274 `AI Check`; no new OSINT |
| 5 | Format | **`deadface{$540000}`** |

## Takeaways

* **"Continuation of X" means reuse X's output.** The expensive steps (GhostTown OSINT, the
  header-truncated JPEG, the GPG dead-drop) were already paid for. The skill here is realising
  you are done mining, not mining harder.
* **Zero-width bait scales.** The same `U+200B`/`U+200C` binary message is pasted into every
  challenge description as an anti-automation troll; a decoy `flag{...}` sits next to it. Decode
  it once, recognise it forever.
* **A "living" target can be a dead end.** Fetching DoomScroll/GhostTown live is the right
  instinct, but when the newest post predates the event content you already have, the puzzle is
  in the files, not the network.
* **Read the column header.** `annual_base_salary_usd` vs `annual_bonus_*` vs
  `transaction_amount_usd` — "salary" is one specific cell, and the CSV deliberately offers
  several tempting dollar amounts per person.

## Tools Used

- The Mark's decrypt chain (GhostTown forum, `libjpeg`/Pillow header-height stego, `cv2.QRCodeDetector`, GnuPG `--pinentry-mode loopback`) — reused, not re-run
- Python for the zero-width binary decode (`U+200B`=0 / `U+200C`=1, 8-bit MSB)
- `curl`/`urllib` against `doomscroll.dctf.io/api/posts` and `ghosttown.deadface.io` to confirm no new material
- Plain reading of `tgri_records.csv`
