# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in nexus-router, please report it responsibly.

**Email:** 64996768+mcp-tool-shop@users.noreply.github.com

**What to include:**
- Description of the vulnerability
- Steps to reproduce
- Affected version(s)
- Potential impact

**Response timeline:**
- Acknowledgement within 48 hours
- Assessment within 7 days
- Fix or mitigation within 30 days for confirmed issues

**Please do NOT:**
- Open a public GitHub issue for security vulnerabilities
- Exploit the vulnerability against other users

## Scope

Nexus-router is an **event-sourced MCP router library** that routes tool calls through adapters with provenance tracking.

- **Data touched:** tool call payloads (routed to adapters), event store (SQLite or in-memory), provenance records (SHA256 digests, append-only), JSON schemas for validation.
- **Data NOT touched:** no network requests by default (adapters may make requests per their own contract), no user credentials, no telemetry.
- **Policy enforcement:** `allow_apply: false` prevents destructive operations, `max_steps` limits execution scope, schema validation rejects malformed requests.
- **Provenance integrity:** SHA256 digests, append-only records, immutable method IDs once defined.
- **No telemetry:** collects nothing, sends nothing.
