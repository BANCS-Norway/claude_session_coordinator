# Security Policy

## Supported Versions

We take security seriously and will address reported vulnerabilities promptly.

| Version | Supported          | Notes                           |
| ------- | ------------------ | ------------------------------- |
| 0.x.x   | :white_check_mark: | Pre-release (internal phase)    |

**Current Status:**

- **Phase 1 (Internal Development):** All reported security issues will be
  addressed
- **Post-1.0 Release:** We will support the latest stable version with
  security updates

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

We strongly prefer private disclosure to protect users while we develop and
deploy fixes.

### Preferred Method: GitHub Security Advisories

Report vulnerabilities via GitHub Security Advisories:

1. Navigate to the [Security tab](https://github.com/BANCS-Norway/claude_session_coordinator/security)
2. Click **"Report a vulnerability"**
3. Fill out the security advisory form with details

### Alternative Method: Email

If you're unable to use GitHub Security Advisories, you can email:

**<security@bancs.no>**

Please encrypt sensitive details using our PGP key if possible.

### What to Include in Your Report

To help us understand and address the vulnerability quickly, please include:

- **Description:** Clear explanation of the vulnerability
- **Steps to Reproduce:** Detailed steps to trigger the issue
- **Proof of Concept:** Code, configuration, or commands demonstrating the vulnerability
- **Impact Assessment:** Your analysis of the potential impact and severity
- **Affected Versions:** Which versions are vulnerable
- **Affected Components:** Which parts of the system (MCP server, storage
  adapters, etc.)
- **Suggested Fix:** If you have ideas for remediation (optional but appreciated)

### Response Timeline

- **Initial Acknowledgment:** Within 72 hours
- **Status Update:** Within 1 week
- **Fix Timeline:** Depends on severity (critical issues prioritized)
  - Critical: Within days
  - High: Within 1-2 weeks
  - Medium/Low: Next scheduled release

## Disclosure Policy

We follow coordinated disclosure principles:

1. **You report** the vulnerability privately (via GitHub Advisory or email)
2. **We acknowledge** receipt and begin investigation
3. **We confirm** the vulnerability and assess severity
4. **We develop** a fix and test thoroughly
5. **We release** a patched version
6. **Public disclosure** occurs after patch is available (typically 90 days
   or when patch is released, whichever comes first)
7. **We credit** security researchers (unless anonymity is requested)

**Embargo Period:**

- Please do not disclose the vulnerability publicly until we've released a fix
- We'll work with you to coordinate public disclosure timing
- We aim to release fixes as quickly as possible while ensuring quality

## Security Considerations for Users

### Storage Security

The Claude Session Coordinator supports multiple storage backends. Each has
different security considerations:

#### Local File Storage

- **Storage Location:** `.claude/session-state/` in project directory
- **File Permissions:** Ensure files are only readable by your user account
  (`chmod 600` or equivalent)
- **Sensitive Data:** Session state may contain sensitive context; consider
  encrypting files at rest
- **Backup Security:** Secure backups appropriately; they contain session data

**Best Practices:**

```bash
# Set restrictive permissions on session state directory
chmod 700 ~/.claude/session-state/

# Set restrictive permissions on individual session files
chmod 600 ~/.claude/session-state/*.json
```

#### Redis Storage

- **Network Security:**
  - Use TLS/SSL for all Redis connections (`rediss://` protocol)
  - Never expose Redis to public internet without authentication
  - Use firewall rules to restrict Redis access

- **Authentication:**
  - Always configure Redis `requirepass` or ACL authentication
  - Use strong, randomly generated passwords
  - Rotate credentials periodically

- **Network Isolation:**
  - Run Redis on localhost or private network
  - Use VPNs or SSH tunnels for remote access
  - Consider network segmentation

- **Data Encryption:**
  - Enable Redis TLS support
  - Consider encryption at rest for sensitive data
  - Use Redis 6+ ACL for fine-grained access control

**Best Practices:**

```bash
# Example secure Redis connection string
rediss://:your-strong-password@localhost:6379/0

# Use environment variables for sensitive configuration
export REDIS_URL="rediss://..."
```

### General Security Best Practices

1. **Credentials:** Never store credentials, API keys, or secrets in session
   state
2. **Environment Variables:** Use environment variables for sensitive
   configuration
3. **Access Control:** Limit access to session state files/databases to
   necessary users only
4. **Dependency Updates:** Keep dependencies updated to receive security patches
5. **Network Exposure:** Don't expose MCP server or storage to untrusted networks
6. **Audit Logs:** Monitor access to session storage for suspicious activity
7. **Data Minimization:** Only store necessary data in session state

### MCP Server Security

- **Local Use:** The MCP server is designed for local development use
- **Network Binding:** Do not bind MCP server to public interfaces
- **Input Validation:** Be cautious with untrusted input in session data
- **Claude Desktop Integration:** Ensure Claude Desktop app is up to date

## Scope

### In Scope

We consider the following in scope for security reports:

- **MCP Server Vulnerabilities:**
  - Code execution vulnerabilities
  - Arbitrary file access
  - Command injection

- **Authentication/Authorization Issues:**
  - Bypass of access controls
  - Privilege escalation

- **Data Exposure:**
  - Unauthorized access to session data
  - Information leakage
  - Privacy violations

- **Injection Vulnerabilities:**
  - Command injection
  - Code injection
  - Path traversal

- **Storage Security:**
  - Insecure storage of sensitive data
  - Insufficient access controls

- **Configuration Issues:**
  - Insecure default configurations
  - Security misconfigurations

### Out of Scope

The following are generally out of scope:

- **Third-Party Dependencies:**
  - Vulnerabilities in upstream dependencies (please report to maintainers)
  - We will address these through dependency updates

- **Physical Access Required:**
  - Issues requiring physical access to the machine

- **Social Engineering:**
  - Attacks relying solely on social engineering

- **Denial of Service:**
  - Local resource exhaustion (designed for local use)
  - Network DoS attacks

- **Theoretical Issues:**
  - Issues without proof of concept or demonstrated impact

- **Expected Behavior:**
  - Features working as designed and documented

**Note:** If you're unsure whether something is in scope, please report it
anyway. We'd rather review it than miss a real issue.

## Security Updates

When we release security updates:

1. **Security Advisory:** We'll publish a GitHub Security Advisory with details
2. **Release Notes:** Security fixes will be highlighted in release notes
3. **CHANGELOG:** Security patches will be documented in CHANGELOG.md
4. **Notifications:** Critical updates will be announced via GitHub releases

## Attribution and Recognition

We deeply appreciate security researchers who help keep our users safe.

**Recognition:**

- Listed in security advisory (if desired)
- Credited in release notes
- Mentioned in CHANGELOG.md
- Public acknowledgment on project website (when available)

**Anonymity:**

- We'll respect requests for anonymous reporting
- You can use a pseudonym or handle
- Let us know your preference when reporting

## Questions?

If you have questions about:

- This security policy
- Whether something qualifies as a security issue
- Our security practices

Please reach out via:

- GitHub Discussions (for general security questions)
- Email: <security@bancs.no> (for confidential inquiries)

## Security Contact

- **Email:** <security@bancs.no>
- **GitHub:** [@BANCS-Norway](https://github.com/BANCS-Norway)
- **Security Advisories:** [Report a vulnerability](https://github.com/BANCS-Norway/claude_session_coordinator/security/advisories/new)

---

**Last Updated:** 2025-10-31

Thank you for helping keep Claude Session Coordinator and its users safe!
