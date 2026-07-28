# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

Do not open public GitHub issues for security vulnerabilities.

Report vulnerabilities privately to the maintainers, including:

- a description of the issue and its impact
- steps to reproduce or a proof of concept
- affected versions, if known

You can expect an acknowledgement within 7 days. We will coordinate a fix and disclosure timeline with you.

## Scope Notes

Talosent runs with the permissions of the user and process that launched it. It does not include a built-in sandbox for tool execution. If you expose the web UI beyond localhost, put it behind authentication and network isolation, and treat API keys in the environment as secrets.
