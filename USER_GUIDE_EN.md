# Local Data Explorer -- User Guide

Local Data Explorer is a tool for **safe exploration of local datasets
and controlled usage of AI models**.

The application analyzes data **locally** and only allows sending
information to AI **after explicit user action**.

Supported file types:

-   CSV
-   TXT
-   MD

------------------------------------------------------------------------

# 1. Core Concept

The application works in three stages:

1.  **Offline data profiling**
    -   dataset statistics
    -   schema inspection
    -   data quality checks
2.  **Offline PII detection**
    -   email
    -   phone number
    -   national ID (RC)
    -   bank account / IBAN
    -   address
    -   name
3.  **Controlled AI usage**
    -   only anonymized datasets can be used
    -   AI is called only when the user explicitly clicks a button

------------------------------------------------------------------------

# 2. Security Model

The application follows strict security rules.

### No automatic AI calls

AI is **never called automatically** when:

-   the application starts
-   a folder changes
-   a file changes
-   filters change

AI is triggered only by the button:

Odeslat do AI / Send to AI

------------------------------------------------------------------------

### Offline data processing

The following operations always run **locally**:

-   dataset profiling
-   PII detection
-   anonymization

Data leaves the machine only during the AI request.

------------------------------------------------------------------------

### Datasets with PII cannot be sent to AI

If personal data is detected:

the original dataset **cannot be sent to AI**.

You must first create an anonymized version.

------------------------------------------------------------------------

# 3. Starting the Application

Recommended method:

Run:

start_data_explorer.bat

Then open:

http://localhost:8501

------------------------------------------------------------------------

### Manual start

pip install -r requirements.txt

streamlit run app.py

------------------------------------------------------------------------

# 4. Selecting Files

1.  Select a folder containing files.
2.  The application scans the folder.
3.  Files appear in the left panel.

Supported filters:

-   file name
-   file type
-   file size
-   modification date

------------------------------------------------------------------------

# 5. Offline Profiling

After selecting a file, the application performs a dataset analysis.

For CSV files it calculates:

-   number of rows
-   number of columns
-   schema
-   missing values
-   numerical statistics
-   duplicate rows
-   top categorical values

For text files it calculates:

-   character count
-   line count
-   word count
-   keyword frequencies

Profiling is performed **locally**.

------------------------------------------------------------------------

# 6. PII Report

The system automatically searches for personal data.

Detected types:

EMAIL\
PHONE\
DOB\
RC\
BANK\
NAME\
ADDRESS

The report displays:

-   PII type
-   row
-   column
-   masked preview
-   detection rule
-   confidence

------------------------------------------------------------------------

# 7. Revealing Values

Click **Show** to temporarily reveal the original value.

Security rules:

-   only one value can be revealed
-   automatically hidden after 30 seconds
-   raw values are never logged

------------------------------------------------------------------------

# 8. Marking False Positives

If a detection is incorrect you can click:

**Mark as safe**

The finding will be ignored for the dataset.

Validity:

-   only for the current file
-   only for the current privacy mode
-   reset when switching files

------------------------------------------------------------------------

# 9. Data Anonymization

Button:

**Anonymize for AI**

This replaces detected PII values with tokens.

Example:

EMAIL → EMAIL_1\
PHONE → PHONE_1\
NAME → NAME_1

Properties:

-   consistent token mapping
-   identical values receive identical tokens
-   mapping is per dataset

------------------------------------------------------------------------

# 10. AI Chat

AI Chat allows dataset analysis using the Mistral model.

AI receives only **metadata**, never the full dataset.

Context options:

schema\
schema + stats\
schema + stats + sample

------------------------------------------------------------------------

# 11. Dataset Sample

Sample size limits:

Strict: 100 rows\
Balanced: 200 rows\
Relaxed: 300 rows

In **Strict mode**, ID-like columns may be removed.

------------------------------------------------------------------------

# 12. AI Context Size Limit

Maximum payload size:

200 KB

If exceeded:

the dataset sample is removed automatically.

Only schema and statistics are sent to the AI.

------------------------------------------------------------------------

# 13. Privacy Modes

### Strict

-   highest detection sensitivity
-   sample max 100 rows
-   removes ID-like columns

### Balanced

-   medium sensitivity
-   sample max 200 rows

### Relaxed

-   lowest sensitivity
-   sample max 300 rows
-   higher risk of missing PII

------------------------------------------------------------------------

# 14. Logging

The system logs only metadata:

-   file selection
-   profiling completion
-   PII detection summary
-   anonymization events
-   AI request metadata

Not logged:

-   dataset content
-   prompts
-   raw personal data

------------------------------------------------------------------------

# 15. Recommended Usage

For real datasets always use:

Strict mode

Send the smallest possible context to AI:

schema\
schema + stats

------------------------------------------------------------------------

# 16. Common Errors

PII detected

Dataset contains personal data.

Solution:

Create an anonymized version.

------------------------------------------------------------------------

Missing MISTRAL_API_KEY

Add the key to:

.env

------------------------------------------------------------------------

No module named 'mistralai'

Install dependencies:

pip install -r requirements.txt
