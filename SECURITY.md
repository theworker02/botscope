# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 2.0.x   | Yes |
| 0.x     | Best-effort (superseded) |

## Reporting a vulnerability

Please report security issues privately via GitHub Security Advisories for this repository, or email the maintainer listed on GitHub (`theworker02`).

Do **not** open a public issue for vulnerabilities.

Include:

- BotScope version
- Environment (`botscope doctor` sanitized output if useful)
- Reproduction steps without sensitive payloads

## Security posture (v2)

- Network contribution is OFF by default
- No unauthorized network scanning features
- Doctor bundles redact common sensitive fields
- Treat confidence scores as heuristics or ML model probabilities, not cryptographic assurances or population prevalences
- Live capture requires explicit authorization
