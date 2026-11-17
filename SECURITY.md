# Security Policy

XenoCode is an early-stage local-first AI coding assistant.

## Supported Versions

The 0.1.x development series is currently maintained.

## Reporting a Vulnerability

Do not publish credentials, private project files or exploit details
in public issues.

Use GitHub private vulnerability reporting if enabled for this
repository. Otherwise, contact the repository maintainer privately
through GitHub.

Include:

- A description of the vulnerability.
- Affected component.
- Reproduction conditions.
- Potential impact.
- Suggested mitigation, if known.

## Current Security Measures

- Workspace path traversal protection.
- Symbolic link rejection.
- Sensitive file filtering.
- Bounded file reads and writes.
- Explicit approval for sensitive tools.
- Restricted arithmetic evaluation.

## Limitations

XenoCode has not undergone an independent security audit.

Do not assume that experimental AI-generated code is safe to execute.
