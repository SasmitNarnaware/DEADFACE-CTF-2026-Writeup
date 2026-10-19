# Deadface 2026 — "File Dump 03"

**Category:** OSINT / Steganography
**Author:** @RP-01
**Points:** 200
**Artifacts:** the same dump as *File Dump 01* / *02* (`File_Dump_Challenge.zip`, 26 files)
**Flag:** `deadface{i_sleep_with_a_nightlight}`

> *"We've got the who. We've got the where. Now we want the deepest, darkest
> secret — the thing he'd never say out loud. It's sitting on some external
> file location."*

---

## TL;DR

1. File Dump 01 gave the member's **handle** (`gh0st404`) and, from the steghide
   payload in `office_memory_meme.jpg`, a pair of **credentials**:
   `ghost404` / `DumpingFiles4funDaily`.
2. File Dump 02 pointed at `technical_details.docx`, which lists an **external FTP
   server**: `45.79.200.170:21` (Linode, `vsFTPd 3.0.5`). The doc coyly says
   *"No credentials are included ... not authorization to access"* — the creds had
   been handed over in challenge 01, this is just the location.
3. Those creds log straight into the FTP home directory. It contains
   `ghost_repo.tar.gz` (an external copy of his personal "persona toolkit" git repo)
   and an empty `test.tft`.
4. The repo's **git history** has a file that was committed and then "removed":
   `notes/personal.txt` — *"remove personal notes - shouldn't have committed that"*.
5. Recovering it from the deleted commit reveals his deepest secret:

   ```
   deadface{i_sleep_with_a_nightlight}
   ```

---

## 1. Putting the previous dumps to work

*File Dump 01* recovered, from the steghide payload in `office_memory_meme.jpg`
(passphrase `n0rth_st4r` from `reminders.docx` metadata):

```
USERNAME: ghost404
PASSWORD: DumpingFiles4funDaily
```

*File Dump 02* identified, in `technical_details.docx`, the only "external" system
in the whole dump:

```
FTP SERVER
Endpoint: 45.79.200.170:21
```

The doc is worded to look like a dead end ("No credentials are included…"), but 01
*did* include credentials, and the challenge prompt says the secret lives on "some
external file location". TCP 21 is open; the banner is `vsFTPd 3.0.5`.

## 2. Logging into the external file location

```python
from ftplib import FTP
ftp = FTP(); ftp.connect("45.79.200.170", 21, timeout=20)
ftp.login("ghost404", "DumpingFiles4funDaily")   # <- from File Dump 01
ftp.set_pasv(True)
ftp.retrlines("LIST", print)
```

```
-rw-r--r-- 1 0 0 16924 Aug 22 23:26 ghost_repo.tar.gz
-rw-r--r-- 1 0 0     0 Aug 22 23:16 test.tft
```

`test.tft` is an empty decoy. `ghost_repo.tar.gz` is the payload — an exported git
repository (`ghost_repo/`) named **hameser-persona toolkit**: his scripts/notes for
"keeping the persona consistent across platforms", with the rule *"keep this repo OFF
the shared drive"*.

## 3. The secret is in the history, not the working tree

The current tree is boring — a README, a `todo.md`, and three stub scripts. The real
answer is buried in git's object store:

```
$ git log --oneline --stat
09986ff add cleanup script
10c40e9 update status in readme
3684e11 remove personal notes - shouldn't have committed that
        notes/personal.txt | 8 --------
b6c56a7 add mailer stub
4d0607f wip notes
        notes/personal.txt | 8 ++++++++
...
```

A file was added in `4d0607f` and deleted four commits later with the confession
*"shouldn't have committed that"*. Deleting a file never removes it from history:

```bash
git show 4d0607f:notes/personal.txt
```

```
note to self (delete this later):

everyone thinks i'm some untouchable ghost in the machine.
the truth, if anyone ever digs this up:

deadface{i_sleep_with_a_nightlight}

the dark just feels like getting caught. ok. back to work.
```

## 4. Answer

```
deadface{i_sleep_with_a_nightlight}
```

---

## Decoys / notes

- `test.tft` — 0-byte file, pure noise (the `.tft` / "test" joke).
- The FTP doc's *"do not interpret this section as authorization"* wording reads like
  a scope warning, but the host is a purpose-built CTF box and the login is supplied
  by challenge 01; reading an anonymous-looking FTP you were given credentials for is
  the intended path.
- `git fsck --lost-found` reports no dangling/unreachable objects — the deleted blob
  is reachable through the parent commit, so `git show <commit>:<path>` is all you need.

## Reproduce

```python
# 1. grab the repo off the external FTP
from ftplib import FTP; import io
ftp = FTP(); ftp.connect("45.79.200.170", 21, timeout=20)
ftp.login("ghost404", "DumpingFiles4funDaily"); ftp.set_pasv(True)
buf = io.BytesIO(); ftp.retrbinary("RETR ghost_repo.tar.gz", buf.write)
open("ghost_repo.tar.gz", "wb").write(buf.getvalue())

# 2. extract, then recover the deleted note from history
import tarfile; tarfile.open("ghost_repo.tar.gz").extractall(".")
# git -C ghost_repo show 4d0607f:notes/personal.txt
```

Helper scripts left in `_tmp/`: `ftp_probe.py`, `ftp_download.py`.
Extracted repo: `_tmp/ftp_dl/ghost_repo/ghost_repo`.
