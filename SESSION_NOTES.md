# ExerciseXCigarXMortality — Session Notes
**Last updated:** April 28, 2026  
**Platform:** All of Us NIH Research Program — Verily Workbench

---

## 1. Workspace & Environment

### Workbench Details
| Field | Value |
|---|---|
| Workspace name | ExerciseXCigarXMortalityAllofUs |
| Workspace ID | exercisexcigarxmortalityallofus |
| Billing project | `wb-smart-aubergine-9536` |
| CDR project | `wb-silky-artichoke-2408` |
| CDR dataset | `wb-silky-artichoke-2408.C2024Q3R8` (cdrv8, released Sept 26 2025) |
| MH supplement | `wb-silky-artichoke-2408.C_V8_R2_offcycle_mhwb` |
| GCS bucket | `gs://cloned-mybucket-wb-smart-aubergine-9536` |
| Service account | `pet-277730803563409la3958@wb-smart-aubergine-9536.iam.gserviceaccount.com` |
| Workbench URL | https://workbench.verily.com/app/... |
| Google project | wb-agile-avocado-3777 (OLD, first workspace — do not use) |

### Environment Initialization (MUST run every session before BigQuery)
```python
import subprocess, os

result = subprocess.run(
    ['bash', '-c', 'source ~/load-env.sh 2>&1 && env'],
    capture_output=True, text=True, cwd=os.path.expanduser("~")
)
for line in result.stdout.split('\n'):
    if '=' in line:
        key, _, val = line.partition('=')
        if any(x in key.upper() for x in ['WORKSPACE', 'GOOGLE', 'CDR', 'BUCKET', 'PROJECT', 'AOU']):
            os.environ[key] = val

PROJECT = os.environ["GOOGLE_PROJECT"]   # wb-smart-aubergine-9536
CDR     = os.environ["WORKSPACE_CDR"]    # wb-silky-artichoke-2408.C2024Q3R8
BUCKET  = os.environ["WORKSPACE_BUCKET"]
CDR_MH  = "wb-silky-artichoke-2408.C_V8_R2_offcycle_mhwb"
```

### BigQuery Client
```python
from google.cloud import bigquery
client = bigquery.Client(project=PROJECT)
```

### Connectivity Test
```python
result = client.query(f"SELECT COUNT(*) as n FROM `{CDR}.person`").to_dataframe()
print(f"Total participants: {result.iloc[0,0]:,}")  # Expected: ~633,547
```

---

## 2. GitHub Repository
- **Repo:** https://github.com/Bigliassi/ExerciseXCigarXMortality (public)
- **Cloned to Workbench:** `~/ExerciseXCigarXMortalityAllofUs/`
- **Clone method:** JupyterLab Git extension (terminal git clone blocked by VPC perimeter)
- **Folder structure:**
  ```
  ExerciseXCigarXMortalityAllofUs/
  ├── notebooks/
  ├── data/
  │   ├── raw/
  │   └── processed/
  ├── scripts/
  └── outputs/
  ```

---

## 3. CDR Database — Confirmed Tables (118 total in C2024Q3R8)

### Key tables for this study
| Table | Purpose |
|---|---|
| `observation` | All survey responses (PPI vocabulary) |
| `person` | Demographics |
| `aou_death` | **Primary mortality table** — 9,429 records (more complete than `death`) |
| `death` | Secondary mortality table — 5,863 records |
| `measurement` | Lab values, vitals |
| `condition_occurrence` | ICD-10 diagnoses |
| `drug_exposure` | Medications, substances |
| `procedure_occurrence` | Procedures |
| `activity_summary` | Fitbit daily activity summaries |
| `steps_intraday` | Fitbit step counts |
| `heart_rate_summary` | Fitbit daily heart rate |
| `heart_rate_minute_level` | Fitbit minute-level HR |
| `sleep_daily_summary` | Fitbit sleep |
| `wear_study` | Wearable study enrollment |
| `survey_conduct` | Survey metadata |
| `zip3_ses_map` | Zip-code SES data |

> **Note:** Use `aou_death` not `death` — it has 60% more records (9,429 vs 5,863).

---

## 4. Confirmed PPI Survey Concept IDs

### Physical Activity — IPAQ (International Physical Activity Questionnaire)
| concept_id | Description | Type |
|---|---|---|
| 1333286 | Vigorous physical activity past 7 days (yes/no) | Question |
| 903631 | Vigorous activity minutes/day | Question |
| 903633 | Vigorous activity hours/day | Question |
| 1333288 | Moderate physical activity past 7 days (yes/no) | Question |
| 1333289 | Walking ≥10 min past 7 days (yes/no) | Question |
| 903630 | Walking minutes/day | Question |
| 903635 | Walking hours/day | Question |
| 1332814 | Physical Activity (topic) | Topic |
| 1333264 | International Physical Activity Questionnaires | Question source |

### Cigar Smoking
| concept_id | Description | Type |
|---|---|---|
| 1586174 | Cigar Smoking: Cigar Smoke Participant | Question |
| 1586175 | Cigar Smoke Participant: Yes | Answer |
| 1586176 | Cigar Smoke Participant: No | Answer |
| 1586177 | Cigar Smoking: Current Cigar Frequency | Question |
| 1586178 | Current Cigar Frequency: Every Day | Answer |
| 1586179 | Current Cigar Frequency: Some Days | Answer |
| 1586180 | Current Cigar Frequency: Not At All | Answer |

### Cigarette Smoking (for confounder control / exclusion of dual users)
| concept_id | Description | Type |
|---|---|---|
| 1585860 | Smoking: Smoke Frequency | Question |
| 1585857 | Smoking: 100 Cigs Lifetime | Question |
| 1585861 | Smoke Frequency: Every Day | Answer |
| 1585862 | Smoke Frequency: Some Days | Answer |
| 1585863 | Smoke Frequency: Not At All | Answer |
| 1585864 | Smoking: Daily Smoke Starting Age | Question |
| 1585873 | Smoking: Number Of Years | Question |
| 1585867 | Smoking: Serious Quit Attempt | Question |

### Other Tobacco (for confounder control)
| concept_id | Description | Type |
|---|---|---|
| 1586166 | Electronic Smoking: Electric Smoke Participant | Question |
| 1586167 | Electric Smoke Participant: Yes | Answer |
| 1586168 | Electric Smoke Participant: No | Answer |
| 1586190 | Smokeless Tobacco: Smokeless Tobacco Participant | Question |
| 1586191 | Smokeless Tobacco Participant: Yes | Answer |
| 1586192 | Smokeless Tobacco Participant: No | Answer |
| 1586182 | Hookah Smoking: Hookah Smoke Participant | Question |
| 1586183 | Hookah Smoke Participant: Yes | Answer |
| 1586184 | Hookah Smoke Participant: No | Answer |

### Mental Health (secondary outcomes — in CDR_MH supplement)
| concept_id | Description |
|---|---|
| To be discovered | PHQ-9 (depression) items |
| To be discovered | GAD-7 (anxiety) items |
| To be discovered | PROMIS items |

---

## 5. Data Coverage (Confirmed Numbers)

| Data Source | Participants |
|---|---|
| Total CDR participants | 633,547 |
| With IPAQ physical activity data | 70,689 |
| With cigar survey data | 575,156 |
| With BOTH IPAQ + cigar data (base cohort) | **69,894** |
| Deaths in base cohort (`death` table) | 575 |
| Deaths in base cohort (`aou_death` table) | **pending** |
| Wearable (activity_summary) | 58,785 |
| Wearable (steps_intraday) | 58,575 |
| Wearable (heart_rate_summary) | 56,261 |
| Wearable (sleep_daily_summary) | 54,322 |
| Wear study enrolled | 40,776 |
| Wearable + cigar overlap | **pending** |

### Cigar smoking distribution (575,156 with data)
| Category | N |
|---|---|
| Ever smoked cigars (Yes) | 213,513 |
| Never smoked cigars (No) | 351,351 |
| Current: Every day | 5,817 |
| Current: Some days | 25,931 |
| Current: Not at all | 185,324 |
| PMI: Skip | 10,325 |

### Other tobacco use (for dual-user exclusion)
| Category | Yes | No |
|---|---|---|
| Electronic smoking | 101,928 | 464,857 |
| Hookah | 101,799 | 463,289 |
| Smokeless tobacco | 53,814 | 513,929 |

---

## 6. Study Design Summary

### Primary Exposures
1. **Physical activity** — IPAQ (vigorous/moderate/walking), wearable steps/HR
2. **Cigar smoking** — ever/never; current frequency (every day / some days / not at all)

### Key Exclusion Criteria (to isolate mechanisms)
- Dual users: cigar + cigarette smokers (identify via concept 1585860)
- Missing data on both PA and cigar exposure

### Primary Outcome
- All-cause mortality — `aou_death` table (preferred over `death`)
- Follow-up window: 2017–2023 (~6 years)

### Secondary Outcomes
- Cardiovascular mortality (cause of death codes)
- Mental health: PHQ-9, GAD-7 (from CDR_MH)
- Quality of life: PROMIS (from CDR_MH)

### Confounders to adjust for
- Age, sex, race/ethnicity (`person` table)
- BMI / physical measurements (`measurement` table)
- Alcohol use (PPI survey)
- Drug use (PPI survey)
- Comorbidities: HTN, diabetes, CVD, COPD (ICD-10 from `condition_occurrence`)
- SES (`zip3_ses_map`, `ds_zip_code_socioeconomic`)
- Sleep (`sleep_daily_summary`)
- Medications (`drug_exposure`)

---

## 7. Next Steps (Pick Up Here)

### Immediate (next session)
- [ ] Run pending query: deaths in base cohort using `aou_death`
- [ ] Run pending query: wearable + cigar overlap size
- [ ] Discover PHQ-9 / GAD-7 / PROMIS concept IDs in `CDR_MH`

### Step 2 — Build master cohort table (`02_cohort_assembly.py`)
Build one wide table per participant combining:
```
person_id | age | sex | race | bmi |
cigar_participant | cigar_frequency |
cigarette_smoker | e_cig | hookah | smokeless |
vigorous_yn | vigorous_min | moderate_yn | moderate_min | walking_yn | walking_min |
steps_daily_avg | hr_resting_avg |
vital_status | death_date | follow_up_days
```

### Step 3 — Define exposure groups
- **PA groups:** Sedentary / Light / Moderate / Vigorous (MET-hour cutoffs)
- **Cigar groups:** Never / Former / Current-occasional / Current-daily
- **Cigar-only flag:** cigar=Yes AND cigarette=Not at all AND e-cig=No AND hookah=No

### Step 4 — Descriptive statistics + balance checks
- Table 1: cohort characteristics by cigar group
- Check confounder distributions across PA × cigar groups

### Step 5 — Survival analysis
- Cox proportional hazards: mortality ~ cigar + PA + confounders
- Kaplan-Meier curves by exposure group
- Dose-response: cigar frequency × PA intensity interaction term

### Step 6 — Secondary outcomes
- Linear/logistic regression for PHQ-9, GAD-7, PROMIS scores
- Mediation analysis (does PA mediate cigar → mortality?)

---

## 8. Working Code Snippets

### Standard session setup (run at top of every notebook)
```python
import subprocess, os, pandas as pd
from google.cloud import bigquery

# Load environment
result = subprocess.run(
    ['bash', '-c', 'source ~/load-env.sh 2>&1 && env'],
    capture_output=True, text=True, cwd=os.path.expanduser("~")
)
for line in result.stdout.split('\n'):
    if '=' in line:
        key, _, val = line.partition('=')
        if any(x in key.upper() for x in ['WORKSPACE','GOOGLE','CDR','BUCKET','PROJECT','AOU']):
            os.environ[key] = val

PROJECT = os.environ["GOOGLE_PROJECT"]
CDR     = os.environ["WORKSPACE_CDR"]
BUCKET  = os.environ["WORKSPACE_BUCKET"]
CDR_MH  = "wb-silky-artichoke-2408.C_V8_R2_offcycle_mhwb"

client  = bigquery.Client(project=PROJECT)
print(f"CDR: {CDR} | Project: {PROJECT}")
```
