# =============================================================================
# 01_cohort_definition.py
# ExerciseXCigarXMortality — All of Us NIH (Verily Workbench)
# Purpose: Environment setup, connectivity check, and initial data pulls
#          to define the study cohort.
#
# CONFIRMED WORKING — April 28, 2026
# CDR: wb-silky-artichoke-2408.C2024Q3R8 (cdrv8)
# Billing project: wb-smart-aubergine-9536
# =============================================================================

# ── Cell 1: Load environment (run this first every session) ─────────────────
import subprocess
import os
import pandas as pd
from google.cloud import bigquery

result = subprocess.run(
    ['bash', '-c', 'source ~/load-env.sh 2>&1 && env'],
    capture_output=True, text=True,
    cwd=os.path.expanduser("~")
)
for line in result.stdout.split('\n'):
    if '=' in line:
        key, _, val = line.partition('=')
        if any(x in key.upper() for x in ['WORKSPACE', 'GOOGLE', 'CDR', 'BUCKET', 'PROJECT', 'AOU']):
            os.environ[key] = val

PROJECT = os.environ["GOOGLE_PROJECT"]    # wb-smart-aubergine-9536
CDR     = os.environ["WORKSPACE_CDR"]     # wb-silky-artichoke-2408.C2024Q3R8
BUCKET  = os.environ["WORKSPACE_BUCKET"]
CDR_MH  = "wb-silky-artichoke-2408.C_V8_R2_offcycle_mhwb"

client = bigquery.Client(project=PROJECT)
print(f"CDR     : {CDR}")
print(f"Project : {PROJECT}")
print(f"Bucket  : {BUCKET}")

# ── Cell 2: Connectivity check ───────────────────────────────────────────────
result = client.query(f"SELECT COUNT(*) as n FROM `{CDR}.person`").to_dataframe()
print(f"Total participants in CDR: {result.iloc[0,0]:,}")   # Expected: ~633,547

# ── Cell 3: Physical activity survey (IPAQ) ──────────────────────────────────
# Confirmed PPI concept IDs for IPAQ physical activity questions
ACTIVITY_CONCEPTS = [
    1333286,  # Vigorous activity past 7 days (yes/no)
    903631,   # Vigorous activity minutes/day
    903633,   # Vigorous activity hours/day
    1333288,  # Moderate activity past 7 days (yes/no)
    1333289,  # Walking >=10 min past 7 days (yes/no)
    903630,   # Walking minutes/day
    903635,   # Walking hours/day
]

activity_sql = f"""
SELECT
    o.person_id,
    c_q.concept_name                                AS question,
    COALESCE(c_a.concept_name, o.value_as_string,
             CAST(o.value_as_number AS STRING))     AS answer,
    o.value_as_number,
    o.observation_date
FROM `{CDR}.observation` o
JOIN `{CDR}.concept` c_q ON o.observation_concept_id = c_q.concept_id
LEFT JOIN `{CDR}.concept` c_a ON o.value_as_concept_id = c_a.concept_id
WHERE o.observation_concept_id IN ({','.join(map(str, ACTIVITY_CONCEPTS))})
ORDER BY o.person_id, o.observation_concept_id
"""

df_activity = client.query(activity_sql).to_dataframe()
print(f"Activity rows: {len(df_activity):,}  |  Unique participants: {df_activity.person_id.nunique():,}")
# Expected: 324,292 rows | 70,689 participants

# ── Cell 4: Cigar smoking survey ─────────────────────────────────────────────
# Confirmed PPI concept IDs for cigar smoking
CIGAR_CONCEPTS = [
    1586174,  # Cigar Smoking: Cigar Smoke Participant (yes/no question)
    1586177,  # Cigar Smoking: Current Cigar Frequency
]

cigar_sql = f"""
SELECT
    o.person_id,
    c_q.concept_name                                AS question,
    COALESCE(c_a.concept_name, o.value_as_string)   AS answer,
    o.value_as_number,
    o.observation_date
FROM `{CDR}.observation` o
JOIN `{CDR}.concept` c_q ON o.observation_concept_id = c_q.concept_id
LEFT JOIN `{CDR}.concept` c_a ON o.value_as_concept_id = c_a.concept_id
WHERE o.observation_concept_id IN ({','.join(map(str, CIGAR_CONCEPTS))})
ORDER BY o.person_id, o.observation_concept_id
"""

df_cigar = client.query(cigar_sql).to_dataframe()
print(f"Cigar rows: {len(df_cigar):,}  |  Unique participants: {df_cigar.person_id.nunique():,}")
print(df_cigar.answer.value_counts())
# Expected: 792,261 rows | 575,156 participants
# Never (No): 351,351 | Ever (Yes): 213,513
# Current daily: 5,817 | Current some days: 25,931

# ── Cell 5: Cigarette + other tobacco (for confounder / dual-user exclusion) ─
OTHER_TOBACCO_CONCEPTS = [
    1585860,  # Smoke Frequency (general cigarettes)
    1585857,  # 100 cigarettes lifetime
    1586166,  # Electronic smoking participant
    1586190,  # Smokeless tobacco participant
    1586182,  # Hookah participant
]

cig_sql = f"""
SELECT
    o.person_id,
    c_q.concept_name                                AS question,
    COALESCE(c_a.concept_name, o.value_as_string)   AS answer,
    o.observation_date
FROM `{CDR}.observation` o
JOIN `{CDR}.concept` c_q ON o.observation_concept_id = c_q.concept_id
LEFT JOIN `{CDR}.concept` c_a ON o.value_as_concept_id = c_a.concept_id
WHERE o.observation_concept_id IN ({','.join(map(str, OTHER_TOBACCO_CONCEPTS))})
ORDER BY o.person_id, o.observation_concept_id
"""

df_other_tobacco = client.query(cig_sql).to_dataframe()
print(f"Other tobacco rows: {len(df_other_tobacco):,}  |  Unique: {df_other_tobacco.person_id.nunique():,}")

# ── Cell 6: Base cohort size check ───────────────────────────────────────────
# Participants with BOTH physical activity (IPAQ) AND cigar survey data
overlap_sql = f"""
SELECT COUNT(DISTINCT pa.person_id) as n_overlap
FROM (
    SELECT DISTINCT person_id FROM `{CDR}.observation`
    WHERE observation_concept_id IN ({','.join(map(str, ACTIVITY_CONCEPTS))})
) pa
JOIN (
    SELECT DISTINCT person_id FROM `{CDR}.observation`
    WHERE observation_concept_id = 1586174
) cig USING (person_id)
"""
r = client.query(overlap_sql).to_dataframe()
print(f"Base cohort (IPAQ + cigar data): {r.iloc[0,0]:,}")   # Expected: 69,894

# ── Cell 7: Mortality data check ─────────────────────────────────────────────
# Use aou_death (9,429 records) — more complete than death table (5,863)
death_sql = f"""
SELECT COUNT(DISTINCT d.person_id) AS cohort_deaths
FROM `{CDR}.aou_death` d
WHERE d.person_id IN (
    SELECT DISTINCT pa.person_id
    FROM (
        SELECT DISTINCT person_id FROM `{CDR}.observation`
        WHERE observation_concept_id IN ({','.join(map(str, ACTIVITY_CONCEPTS))})
    ) pa
    JOIN (
        SELECT DISTINCT person_id FROM `{CDR}.observation`
        WHERE observation_concept_id = 1586174
    ) cig USING (person_id)
)
"""
r = client.query(death_sql).to_dataframe()
print(f"Deaths in base cohort (aou_death): {r.iloc[0,0]:,}")

# ── Cell 8: Wearable cohort overlap ──────────────────────────────────────────
# How many cigar-survey participants also have wearable data?
# (potential larger cohort using objective PA instead of IPAQ)
wearable_sql = f"""
WITH cigar_pids AS (
    SELECT DISTINCT person_id FROM `{CDR}.observation`
    WHERE observation_concept_id = 1586174
)
SELECT COUNT(DISTINCT a.person_id) AS wearable_plus_cigar
FROM `{CDR}.activity_summary` a
JOIN cigar_pids c ON a.person_id = c.person_id
"""
r = client.query(wearable_sql).to_dataframe()
print(f"Wearable + cigar survey overlap: {r.iloc[0,0]:,}")

# =============================================================================
# NEXT: 02_cohort_assembly.py
# Build wide master table per participant with all exposures,
# covariates, vital status, and follow-up time.
# =============================================================================
