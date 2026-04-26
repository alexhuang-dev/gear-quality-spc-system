# Security Policy

## Supported Versions

The latest tagged release is supported. Older releases may receive fixes when the issue is small and low-risk.

## Data And Secrets

This project is a gear inspection quality analysis system. Do not commit:

- `.env` files
- API keys or model provider tokens
- production measurement data
- customer, supplier, or part-identifying datasets
- generated reports containing proprietary inspection results
- SQLite databases or runtime artifacts

Use synthetic or anonymized CSV samples for examples, tests, and public issues.

## Runtime Boundary

The system analyzes inspection data and generates reports. It does not directly control production equipment, PLCs, MES, ERP, SCADA, or actuator systems.

Before connecting it to production infrastructure, add environment-specific controls such as authentication, authorization, audit logs, network segmentation, rate limits, retention rules, and review of exported reports.

## Reporting A Vulnerability

Please open a private security advisory on GitHub if available, or contact the repository owner through GitHub. Include:

- affected version or commit
- reproduction steps
- expected and actual behavior
- whether private inspection data, credentials, or generated reports can be exposed or modified
