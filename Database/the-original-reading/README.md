# DEADFACE CTF Writeup — The Original Reading

**Category:** Database / SQL  
**Difficulty:** 70 points  
**Challenge author:** `syyntax`

## Challenge Description

Aurora Pharmaceuticals ran a Phase III clinical trial for a drug called Veltrexa. The trial's electronic data capture (EDC) system maintained an audit trail in a `data_changes` table. One entry had modified a primary efficacy endpoint, and the objective was to recover its original value.

## Solution

### Step 1: Explore the available databases

After connecting to the provided MySQL shell, I listed the available databases:

```sql
SHOW DATABASES;
```

The output included `aurora_audit`, `aurora_ehr`, `aurora_pharmacy`, and `aurora_trials`.

### Step 2: Select the clinical trials database

Since the challenge involved a Phase III clinical trial, I selected `aurora_trials`:

```sql
USE aurora_trials;
```

Then I listed its tables:

```sql
SHOW TABLES;
```

The database contained the following tables:

- `adverse_events`
- `data_changes`
- `results`
- `sites`
- `studies`
- `subjects`

The `data_changes` table was the key to recovering the overwritten value.

### Step 3: Inspect the audit table schema

I examined the table structure:

```sql
DESCRIBE data_changes;
```

The relevant columns were:

- `table_name` — the table containing the modified record
- `record_ref` — the reference identifying the record
- `field_name` — the modified field
- `old_value` — the value before the change
- `new_value` — the value after the change
- `reason` — the recorded reason for the modification

The `old_value` column was particularly important because the challenge asked for the original reading.

### Step 4: Search for the modified efficacy endpoint

I queried the audit trail for fields containing `efficacy` or `endpoint`:

```sql
SELECT *
FROM data_changes
WHERE field_name LIKE '%efficacy%'
   OR field_name LIKE '%endpoint%';
```

The query returned one matching record:

| Field | Value |
|---|---|
| `change_id` | `500001` |
| `study_id` | `1` |
| `table_name` | `results` |
| `record_ref` | `VELT-0137` |
| `field_name` | `primary_efficacy_delta` |
| `old_value` | `2.3` |
| `new_value` | `6.0` |
| `changed_by` | `mreyes` |
| `changed_at` | `2025-12-06 23:14:00` |
| `reason` | `Query resolution per monitor` |

### Step 5: Recover the original value

The audit record showed that `primary_efficacy_delta` for record `VELT-0137` had changed from `2.3` to `6.0`.

Since the challenge required the original value, I used the `old_value` field rather than the modified `new_value`.

**Original value:** `2.3`

## Flag

```text
deadface{2.3}
```

## Key Takeaway

This challenge demonstrates how SQL audit trails can reveal previous values of modified records. Even when a database field has been changed, an audit table that preserves the old and new values can help reconstruct the original data.