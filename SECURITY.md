# Security Policy

## Security Surface

AMC is a web application for practice math tests. Primary security concerns:

- Authentication bypass or session hijacking (student/teacher role separation)
- Injection attacks against math problem parsing logic (LaTeX/expression input)
- Supply-chain attacks via GitHub Actions workflow manipulation
- Credential exposure via environment variable leakage in CI/CD
- Insecure direct object references on student answer and score endpoints

Mitigations include signed commits (required_signatures ruleset), required-status-check
rulesets, Bandit static analysis, OSV-Scanner dependency scanning, ClusterFuzzLite
on input validation paths, and REUSE license compliance checks.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.0   | Yes       |

## Reporting a Vulnerability

Do not open a public GitHub issue for security vulnerabilities.

To report a vulnerability privately, use GitHub's
[Private Vulnerability Reporting](https://github.com/ByronWilliamsCPA/AMC/security/advisories/new)
feature.

Or email: [byronawilliams@gmail.com](mailto:byronawilliams@gmail.com)

## Response Timeline

We commit to providing an initial response to all vulnerability reports within 14 days of submission.

- Acknowledgement: within 48 hours
- Initial assessment: within 5 business days
- Resolution target: 30 days for critical, 90 days for others

## Organization Policy

See also: [ByronWilliamsCPA organization security policy](https://github.com/ByronWilliamsCPA/.github/blob/main/SECURITY.md)
