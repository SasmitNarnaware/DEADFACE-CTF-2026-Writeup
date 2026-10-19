# DEADFACE CTF 2026 — Aurora Health Compromised Account — Writeup

**Challenge:** Aurora Health incident response — compromised account
**Category:** SQL / Forensics
**Artifact:** Provided MySQL shell at `https://aurora.dctf.io/`
**Database of interest:** `aurora_audit` (tables `users`, `access_log`)
**Flag:** `deadface{kbhatt}`

---

## 0. TL;DR

1. Connect to the provided MySQL shell and inspect the `aurora_audit` database.
2. `access_log` records user activity with `user_id`, `workstation`, and `accessed_at`.
3. Find accounts whose same `accessed_at` timestamp appears on more than one workstation:
   ```sql
   SELECT user_id, accessed_at, COUNT(DISTINCT workstation) ws,
          GROUP_CONCAT(DISTINCT workstation) wss
   FROM aurora_audit.access_log
   GROUP BY user_id, accessed_at
   HAVING ws > 1
   ORDER BY accessed_at;
   ```
4. Only `user_id = 16` repeatedly appears on two different workstations at the exact same timestamp (8 occurrences).
5. Resolve the user:
   ```sql
   SELECT username FROM aurora_audit.users WHERE user_id = 16;
   ```
   Result: `kbhatt`.

```text
deadface{kbhatt}
```

---

## 1. Connecting to the provided MySQL shell

The challenge provides a browser-based terminal running:

```text
mysql --no-defaults --host=aurora-mysql --port=3306 --user=player ...
```

After connecting, list databases:

```sql
SHOW DATABASES;
```

Relevant databases include `aurora_audit`, `aurora_ehr`, `aurora_pharmacy`, and `aurora_trials`. The incident is about account activity, so `aurora_audit` is the target.

---

## 2. Schema

```sql
SHOW COLUMNS FROM aurora_audit.access_log;
SHOW COLUMNS FROM aurora_audit.users;
```

`access_log`:

| Field | Type |
|---|---|
| log_id | bigint |
| user_id | int |
| patient_mrn | varchar(16) |
| patient_id | int |
| action | varchar(20) |
| resource | varchar(30) |
| ip_address | varchar(20) |
| workstation | varchar(20) |
| accessed_at | datetime |

`users`:

| Field | Type |
|---|---|
| user_id | int |
| username | varchar(40) |
| full_name | varchar(80) |
| role | varchar(50) |
| department | varchar(50) |
| status | varchar(20) |
| created_at | datetime |
| handler_ref | varchar(16) |

---

## 3. Finding the compromised account

The clue is one legitimate account used from two places at once: its login/activity appears on two different workstations at the very same timestamp, repeatedly.

Group activity by account and timestamp, then require more than one distinct workstation:

```sql
SELECT user_id, accessed_at,
       COUNT(DISTINCT workstation) AS ws,
       GROUP_CONCAT(DISTINCT workstation) AS workstations
FROM aurora_audit.access_log
GROUP BY user_id, accessed_at
HAVING COUNT(DISTINCT workstation) > 1
ORDER BY accessed_at;
```

Result (abridged):

| user_id | accessed_at | ws | workstations |
|---:|---|---:|---|
| 16 | 2025-11-04 23:54:03 | 2 | WS-008,WS-028 |
| 16 | 2025-11-05 23:55:55 | 2 | WS-013,WS-025 |
| 16 | 2025-11-14 02:18:01 | 2 | WS-002,WS-023 |
| 16 | 2025-11-18 01:23:54 | 2 | WS-015,WS-027 |
| 16 | 2025-11-19 02:37:21 | 2 | WS-008,WS-026 |
| 16 | 2025-11-21 02:51:31 | 2 | WS-018,WS-029 |
| 16 | 2025-11-23 02:29:51 | 2 | WS-006,WS-030 |
| 16 | 2025-11-27 03:57:17 | 2 | WS-011,WS-022 |

Confirm that only one account has this pattern:

```sql
SELECT user_id, COUNT(*) AS suspicious_pairs
FROM (
    SELECT user_id, accessed_at
    FROM aurora_audit.access_log
    GROUP BY user_id, accessed_at
    HAVING COUNT(DISTINCT workstation) > 1
) t
GROUP BY user_id;
```

Result:

| user_id | suspicious_pairs |
|---:|---:|
| 16 | 8 |

Resolve the username:

```sql
SELECT user_id, username, full_name, role, status
FROM aurora_audit.users
WHERE user_id = 16;
```

Result:

| user_id | username | full_name | role | status |
|---:|---|---|---|---|
| 16 | kbhatt | Kavya Bhatt | Registered Nurse | active |

---

## 4. Answer

The compromised account is `kbhatt`.

```text
deadface{kbhatt}
```