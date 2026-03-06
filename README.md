# Local Data Explorer

Local Data Explorer is a **privacy-first data exploration tool** for working with local datasets and AI.

The application performs **offline data profiling and PII detection**, and only allows sending data to an LLM after explicit user action.

The project focuses on **safe AI usage with sensitive data**.

---

# Features

* Local dataset exploration
* Offline PII detection
* One-click anonymization
* Controlled AI analysis
* Privacy modes
* Payload size guard
* Local audit logging

Supported file types:

```
CSV
TXT
MD
```

---

# Architecture

Pipeline:

```
dataset
↓
offline profiling
↓
PII detection
↓
(optional) anonymization
↓
context builder
↓
LLM request
```

AI is **never called automatically**.

---

# Security Model

The application follows these rules:

* AI is called **only via explicit user action**
* raw datasets **never leave the machine automatically**
* datasets containing PII **must be anonymized first**
* logs never contain dataset content or prompts

---

# Installation

Clone the repository:

```
git clone <repo>
cd data-explorer
```

Install dependencies:

```
pip install -r requirements.txt
```

---

# Configuration

Create `.env`:

```
MISTRAL_API_KEY=your_key_here
```

---

# Running the Application

Recommended:

```
start_data_explorer.bat
```

or manually:

```
streamlit run app.py
```

Application runs at:

```
http://localhost:8501
```

---

# Privacy Modes

Strict

* highest detection sensitivity
* sample limit: 100 rows
* removes ID-like columns

Balanced

* medium detection sensitivity
* sample limit: 200 rows

Relaxed

* minimal detection
* sample limit: 300 rows

---

# AI Context Scope

The LLM receives only metadata:

```
schema
schema + stats
schema + stats + sample
```

---

# Payload Size Limit

Maximum AI payload size:

```
200 KB
```

If exceeded:

```
sample is removed automatically
```

---

# Logging

Logged events:

* file selection
* profiling completed
* PII detection summary
* anonymization events
* AI request metadata

Not logged:

* dataset content
* prompts
* raw PII values

---

# Project Goal

The goal of this project is to provide a **safe interface between local datasets and AI models**.

This helps prevent accidental exposure of personal or sensitive information.

---

# License

MIT
