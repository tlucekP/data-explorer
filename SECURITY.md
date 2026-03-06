# Security Policy

## Security Model

Local Data Explorer is designed to prevent accidental exposure of sensitive data when interacting with AI systems.

The application enforces several safeguards:

* AI requests are never executed automatically.
* Data is processed locally before any AI interaction.
* Datasets containing detected PII cannot be sent to the AI in their original form.
* Users must explicitly anonymize the dataset before AI usage.

## Data Handling

Sensitive operations are executed locally:

* dataset profiling
* PII detection
* anonymization

Only a minimal metadata context is sent to the AI.

The context may include:

* schema
* aggregated statistics
* small anonymized samples

## Logging

Logs intentionally exclude:

* dataset contents
* user prompts
* raw PII values

Logs contain only operational metadata.

## Payload Protection

AI payload size is limited to prevent large data leaks.

If the payload exceeds the limit:

```
dataset sample is removed
```

and only metadata is sent.

## Responsible Disclosure

If you discover a security issue, please report it responsibly by opening a private issue in the repository.
