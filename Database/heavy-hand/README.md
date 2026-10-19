# Deadface CTF — Heavy Hand

**Category:** SQL / Database  
**Difficulty:** 100 points  
**Challenge Author:** syyntax

## Objective

Identify the prescriber who dispensed the highest total quantity of Schedule II medication between October 1, 2025, and December 31, 2025, using the `aurora_pharmacy` database. Submit their DEA number.

## Step 1: Explore the database

Connected to the provided MySQL shell and listed the available databases.

```sql
SHOW DATABASES;
```

Selected the pharmacy database and listed its tables.

```sql
USE aurora_pharmacy;
SHOW TABLES;
```

The database contained the following relevant tables:

- `dispenses`
- `prescriptions`
- `drugs`
- `prescribers`

## Step 2: Inspect the table structures

Used `DESCRIBE` to understand the database schema and identify the relevant columns.

```sql
DESCRIBE dispenses;
DESCRIBE prescriptions;
DESCRIBE drugs;
DESCRIBE prescribers;
```

The important columns were:

| Table | Relevant columns |
|---|---|
| `dispenses` | `rx_id`, `quantity_dispensed`, `dispensed_at` |
| `prescriptions` | `rx_id`, `prescriber_id`, `drug_id` |
| `drugs` | `drug_id`, `dea_schedule` |
| `prescribers` | `prescriber_id`, `dea_number` |

These tables could be joined through their shared IDs to connect dispense records to prescriptions, drugs, and prescribers.

## Step 3: Query the data

Wrote a SQL query to filter Schedule II drugs dispensed during the final quarter of 2025, calculate the total quantity for each prescriber, and sort the results in descending order.

```sql
SELECT
    p.prescriber_id,
    p.dea_number,
    SUM(d.quantity_dispensed) AS total_quantity
FROM dispenses d
JOIN prescriptions rx
    ON d.rx_id = rx.rx_id
JOIN drugs dr
    ON rx.drug_id = dr.drug_id
JOIN prescribers p
    ON rx.prescriber_id = p.prescriber_id
WHERE d.dispensed_at >= '2025-10-01'
  AND d.dispensed_at < '2026-01-01'
  AND dr.dea_schedule = 'II'
GROUP BY p.prescriber_id, p.dea_number
ORDER BY total_quantity DESC
LIMIT 1;
```

### How the query works

1. **JOIN:** Connects dispense records to prescriptions, drugs, and prescribers.
2. **Date filter:** Includes dispensing records from October 1 through December 31, 2025. The exclusive upper bound includes all times on December 31.
3. **Schedule filter:** Restricts the results to drugs classified as Schedule II.
4. **SUM:** Calculates the total quantity actually dispensed by each prescriber.
5. **GROUP BY:** Groups the results by prescriber.
6. **ORDER BY and LIMIT:** Sorts the highest total first and returns the top result.

## Step 4: Analyze the results

The query returned the following result:

| Field | Result |
|---|---|
| Prescriber ID | `2` |
| DEA number | `BR2938471` |
| Total quantity dispensed | `5220` |

Prescriber ID `2` had the highest total quantity of Schedule II medication dispensed during the specified period.

## Final Flag

```text
deadface{BR2938471}
```

## Conclusion

The challenge was solved by exploring the pharmacy database, identifying the relationships between its tables, and using SQL joins, date filtering, aggregation, and sorting to determine which prescriber had the highest total quantity of Schedule II medication dispensed in Q4 2025.