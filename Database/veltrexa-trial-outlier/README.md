# DEADFACE CTF 2026 — Veltrexa Trial Outlier (Database)

| | |
|---|---|
| **Category** | Database / SQL |
| **Database** | `aurora_trials` |
| **Flag** | `deadface{VELT-0148}` |

---

## 1. Challenge Overview

# Veltrexa Trial Outlier Writeup

## Challenge

The Veltrexa trial data contains a fabricated efficacy value. One subject's recorded
primary endpoint improvement is more than three standard deviations above the
study-wide mean. Identify that subject's code.

## Access

Connected to the provided MySQL shell at `aurora.dctf.io`:

```sql
SHOW DATABASES;
USE aurora_trials;
SHOW TABLES;
```

Relevant tables:

- `studies`
- `subjects`
- `results`
- `data_changes`

## Schema and study

The trial database contains one study:

```sql
SELECT * FROM studies;
```

- Protocol: `AUR-VLT-3001`
- Drug: Veltrexa (velcoraxine)
- Status: data locked
- Data lock date: `2025-12-01`

Subjects: 60 total, split evenly between treatment and placebo.

Results contain two measures:

- `primary_efficacy_delta`
- `secondary_qol_score`

The primary endpoint is `primary_efficacy_delta`, with one `Week 24` value per subject.

## Statistical outlier

Compute the study-wide mean and standard deviation for the primary endpoint:

```sql
SELECT
  AVG(value) AS mean,
  STDDEV_POP(value) AS sd,
  MAX(value) AS max_value
FROM results
WHERE measure = 'primary_efficacy_delta';
```

Result:

- Mean: `2.965`
- Population SD: `2.8067`
- Maximum value: `22.00`

The three-sigma threshold is:

```text
mean + 3 * sd = 2.965 + 3 * 2.8067 = 11.385
```

Only one value exceeds this threshold. Identify the subject:

```sql
SELECT s.subject_code, s.arm, r.value
FROM results r
JOIN subjects s ON s.subject_id = r.subject_id
WHERE r.measure = 'primary_efficacy_delta'
  AND r.value > 11;
```

Result:

| subject_code | arm     | value |
|--------------|---------|-------|
| VELT-0148    | placebo | 22.00 |

The z-score for this value is approximately `6.78`, far beyond three standard deviations.

## Post-lock context

The `data_changes` table also records a post-lock modification:

- `VELT-0137`
- `primary_efficacy_delta`
- `2.3 -> 6.0`
- Changed by `mreyes`
- Changed at `2025-12-06 23:14:00`

This is the known post-lock edit, but it is not the statistical outlier. The separate fabricated value is the `22.00` entry for `VELT-0148`.

## Answer

```text
deadface{VELT-0148}
```


---

## 2. Statistical Outlier Methodology (Three-Sigma Rule)

Writeup: Veltrexa Trial Outlier
Overview
The challenge states that one subject’s recorded efficacy improvement is statistically impossible: it lies more than three standard deviations above the study-wide mean for the primary endpoint. In a real clinical dataset, such an extreme value is a strong indicator of fabricated data rather than a genuine measurement.

The goal is to query the MySQL/MariaDB database, calculate the mean and standard deviation of the primary efficacy endpoint, and identify the subject whose value exceeds:

𝜇
+
3
𝜎
μ+3σ
where 
𝜇
μ is the study-wide mean and 
𝜎
σ is the standard deviation.

Reconnaissance
After connecting to the database, the first step is to enumerate the available tables:

sql
SHOW TABLES;
This reveals the trial-related tables. The next step is to inspect the schema of the table containing efficacy results:

sql
DESCRIBE <efficacy_table>;
Look for columns such as:

subject_code or subject_id

efficacy_improvement, primary_endpoint, score, or a similarly named efficacy metric

Possibly visit, treatment-arm, or measurement-date columns

Identifying the Outlier
If each subject has one efficacy value, the direct query is:

sql
SELECT subject_code, efficacy_value
FROM efficacy_table
WHERE efficacy_value > (
    SELECT AVG(efficacy_value) + 3 * STDDEV_SAMP(efficacy_value)
    FROM efficacy_table
);
This returns only subjects whose efficacy value is greater than three sample standard deviations above the overall mean.

If efficacy is recorded across multiple visits or measurements, first calculate each subject’s average improvement, then compare those subject-level means against the study-wide distribution:

sql
WITH subject_means AS (
    SELECT
        subject_code,
        AVG(efficacy_value) AS mean_efficacy
    FROM efficacy_table
    GROUP BY subject_code
)
SELECT
    subject_code,
    mean_efficacy
FROM subject_means
WHERE mean_efficacy > (
    SELECT AVG(mean_efficacy) + 3 * STDDEV_SAMP(mean_efficacy)
    FROM subject_means
);
Only one subject should remain after applying the three-sigma threshold.

Result
The query identifies a single anomalous subject whose efficacy improvement is more than three standard deviations above the study-wide mean. This subject’s code is the flag value.

The flag is submitted in the required format:

text
deadface{SUBJECT_CODE}
Takeaway
Statistical outlier detection is a useful forensic technique in data-integrity investigations. A value beyond three standard deviations from the mean is not proof of fraud by itself, but in a controlled clinical-trial context—especially alongside other evidence such as an improper post-lock edit—it is a meaningful signal that the record may have been manually altered or invented.
