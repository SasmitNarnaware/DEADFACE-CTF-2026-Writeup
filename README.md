# DEADFACE CTF 2026 — Challenges & Writeups

[![CTF](https://img.shields.io/badge/CTF-DEADFACE%202026-red.svg)](https://deadface.io)
[![Challenges](https://img.shields.io/badge/Challenges-39%20Solved-brightgreen.svg)](#challenge-index)

This repository contains problem files, challenge binaries, pcaps, forensic artifacts, solve scripts, and detailed writeups for **DEADFACE CTF 2026**.

All challenges are organized strictly by category, with only the necessary challenge files and clean writeups (no temporary dumps or scratch scripts).

---

## Repository Structure

```text
DEADFACE-CTF-2026/
├── Cryptography/              # Stream cipher keystream reuse, cryptoanalysis
├── Database/                  # Aurora Health MySQL audit logs, pharmacy dispenses & clinical trial data
├── Exploitation/              # Linux privilege escalation, credential harvesting from shell history
├── Forensics/                 # ICMP tunneling, EXIF metadata, PNG steganography & forgery
├── Medical-Device-IoT/        # Emedra CerebraScan CS-9000 hospital device exploitation suite
├── Mobile-Security/           # Android (De Monne Financial APK) & iOS (Aurora Patient Portal IPA)
├── OSINT/                     # GhostTown forum, DoomScroll API, transportation records, historic squares
├── Reverse-Engineering/       # Cereal Killer series (x86 ELF, PE32, .NET reflection loaders)
├── Steganography/             # LSB image embedding, file carvers, hidden headers
└── Web-Exploitation/          # Health Spark fax portal, IDOR, SQL injection, JWT abuse
```

---

## Challenge Index

| Category | Challenge Name | Problem Files | Solved Flag |
|---|---|---|---|
| **Cryptography** | [Infrequent Emojis](./Cryptography/infrequent-emojis/README.md) | `infrequent-emojis.png` | `deadface{please_try_out_my_new_standard}` |
| **Cryptography** | [Second Shift](./Cryptography/second-shift/README.md) | `relay-heartbeat.enc`, `relay-heartbeat.json`, `relay-tasking.enc`, `solve.py` | `deadface{ctr_nonce_reuse_breaks_confidentiality}` |
| **Database** | [Aurora Health Compromised Account](./Database/aurora-compromised-account/README.md) | *None (Remote MySQL)* | `deadface{kbhatt}` |
| **Database** | [Heavy Hand](./Database/heavy-hand/README.md) | *None (Remote MySQL)* | `deadface{BR2938471}` |
| **Database** | [The Original Reading](./Database/the-original-reading/README.md) | *None (Remote MySQL)* | `deadface{2.3}` |
| **Database** | [Veltrexa Trial Outlier](./Database/veltrexa-trial-outlier/README.md) | *None (Remote MySQL)* | `deadface{VELT-0148}` |
| **Exploitation** | [Hostbuster](./Exploitation/hostbuster/README.md) | *None (Lab Shell)* | `deadface{f00th0ld_0n_ch4r0n}` / `deadface{h1st0ry_r3m3mb3rs_4ll}` |
| **Forensics** | [Art Heist: The Forgery](./Forensics/art-heist-the-forgery/README.md) | `CTF_Forgery_Paintings.zip` | `deadface{L4MIA_SIGNS_HER_WORK}` |
| **Forensics** | [Data Go Brrrrr](./Forensics/data-go-brrrrr/README.md) | `PCAP01.pcap`, `solve.py` | `deadface{icmp_3xfil_wh3n_th3y_least_susp3ct}` |
| **Forensics** | [Exifltration](./Forensics/efixletration/README.md) | `exfiltration.zip` | `deadface{timing-is-everything}` |
| **Medical-Device-IoT** | [Bedside Manner](./Medical-Device-IoT/bedside-manner/README.md) | `cs9000-field-service-manual.pdf` | `deadface{d3fault_cr3ds_n3v3r_ch4ng3d}` |
| **Medical-Device-IoT** | [Dump It](./Medical-Device-IoT/dump-it/README.md) | `cs9000-field-service-manual.pdf` | `deadface{un10ck3d_k10sk_qu4cks_b4ck}` |
| **Medical-Device-IoT** | [Factory Settings](./Medical-Device-IoT/factory-settings/README.md) | `cs9000-field-service-manual.pdf` | `deadface{v13w_s0urc3_sav3s_l1v3s}` |
| **Medical-Device-IoT** | [Live Boot](./Medical-Device-IoT/live-boot/README.md) | `cs9000-field-service-manual.pdf` | `deadface{h4rdc0d3d_k3ys_1n_th3_c0nf1g}` |
| **Medical-Device-IoT** | [Second Opinion](./Medical-Device-IoT/second-opinion/README.md) | `cs9000-field-service-manual.pdf` | `deadface{hdm1_l34ks_th3_wh0l3_p4t13nt}` |
| **Mobile-Security** | [Diagnosis](./Mobile-Security/diagnosis/README.md) | `app-release.apk` | `deadface{flaG_ManIfesT3d}` |
| **Mobile-Security** | [Hard Kept Secrets](./Mobile-Security/hard-kept-secrets/README.md) | `app-release.apk`, `solve.py` | `deadface{zqJRlVwBA9Xm2lE5EPjgbj/4rOxlkYZgDtkdP7jV80rZgLFrlnOEn+VAu31YKQrR}` |
| **Mobile-Security** | [Inside Man](./Mobile-Security/inside-man/README.md) | `app-release.apk`, `solve.py` | `deadface{l3FT_b3Hind!}` |
| **Mobile-Security** | [No Holding Back](./Mobile-Security/no-holding-back/README.md) | `app-release.apk`, `solve.py` | `deadface{IDOR_u_2_f1nD_m0r3_Fl4gz}` |
| **Mobile-Security** | [Aurora Patient Portal: Info Leak](./Mobile-Security/aurora-patient-portal-info-leak/README.md) | `AuroraPatientPortal.ipa.zip` | `deadface{Mara-Voss-1988-04-17}` |
| **Mobile-Security** | [Aurora Patient Portal: Patient ID](./Mobile-Security/aurora-patient-id/README.md) | `AuroraPatientPortal.ipa.zip` | `deadface{PID-847261}` |
| **Mobile-Security** | [Aurora Patient Portal: Gateway Server](./Mobile-Security/aurora-gateway-server/README.md) | `AuroraPatientPortal.ipa.zip` | `deadface{gw-westlake-int-03}` |
| **Mobile-Security** | [SQL Skillz](./Mobile-Security/sql-skillz/README.md) | `AuroraPatientPortal.ipa.zip` | `deadface{Candesartan}` |
| **OSINT** | [Car Crash](./OSINT/car-crash/README.md) | `14876559-99c8-4f1d-ba01-42bce7ec374d.jpg` (`car_crash.jpg`) | `deadface{08_10_1961}` |
| **OSINT** | [Chatty Cathy](./OSINT/chatty-cathy/README.md) | *None (Remote Target)* | `deadface{y0u_m3ddling_k!ds}` |
| **OSINT** | [File Dump 02](./OSINT/file-dump-02/README.md) | *None (Image Archive)* | `deadface{alaska_macstore}` |
| **OSINT** | [File Dump 03](./OSINT/file-dump-03/README.md) | *None (Image Archive)* | `deadface{i_sleep_with_a_nightlight}` |
| **OSINT** | [Get That Bag](./OSINT/get-that-bag/README.md) | `tgri_records.csv` | `deadface{$540000}` |
| **OSINT** | [Ghost of Squares Past](./OSINT/ghost-of-squares-past/README.md) | *None (Historic District OSINT)* | `deadface{1733-1742-1815-1733-gordon}` |
| **OSINT** | [The Mark](./OSINT/the-mark/README.md) | `bigdawg-1.jpg`, `tgri_records.csv.gpg` | `deadface{Santos_Staudenmaier}` |
| **OSINT** | [The Vibes Are Freaking Me Out](./OSINT/the-vibes-are-freaking-me-out/README.md) | *None (GhostTown / Extension)* | `deadface{A11_Th1s_Pr0mpt1ng_G3ts_M3_N0wh3r3!}` |
| **OSINT** | [Travel Destinations](./OSINT/travel-destinations/README.md) | *None (GhostTown Forum)* | `deadface{y0u_m3ddling_k!ds}` |
| **OSINT** | [You Wouldn't Git It](./OSINT/you-wouldnt-git-it/README.md) | *None (DoomScroll / GhostTown)* | `deadface{13_h4ck3r5_walk3d_int0_a_bar_each_says_Ill_h4v3_a_r00t_b33r}` |
| **Reverse-Engineering** | [RE01 - Cereal Killer 01 (Insectoids)](./Reverse-Engineering/re01-cereal-killer-01-insectoids/README.md) | `re01-win-x86.exe` | `deadface{You-Vill-Eat-Ze-Bugz-Und-You-Vill-Be-Happy!!!}` |
| **Reverse-Engineering** | [RE03 - Spooky Cereals: The Nordics](./Reverse-Engineering/re03-spooky-cereals-the-nordics/README.md) | `re03-ck02.7z`, `re03-lin-x86.bin`, `re03-win-x86.exe`, `KlippyAI-trained-on-CK02.exe` | `deadface{N0rdics-R3ally-like-Frank3nb3rry-cuz-bro-is-tall-like-they-are!}` |
| **Reverse-Engineering** | [RE05 - Spooky Cereals: The Greys](./Reverse-Engineering/re05-spooky-cereals-the-greys/README.md) | `inner.dll` | `deadface{Before_Consenting_to_Med_Exam_Ascertain_Destination_of_Finger!}` |
| **Steganography** | [File Dump 01](./Steganography/file-dump-01/README.md) | `File_Dump_Challenge.zip` | `deadface{gh0st404}` |
| **Steganography** | [Headshot](./Steganography/headshot/README.md) | `headshot.zip` | `deadface{b00m_h34Dsh0TTT}` |
| **Web-Exploitation** | [Do People Still Fax in 2026?](./Web-Exploitation/do-people-still-fax-in-2026/README.md) | *None (Remote Web Portal)* | `deadface{someone_should_report_this}` |
| **Web-Exploitation** | [I Want to be a Real Boy](./Web-Exploitation/i-want-to-be-a-real-boy/README.md) | *None (Remote Web Portal)* | `deadface{oh_you_shouldnt_be_here}` |

---

Happy Learning :)
