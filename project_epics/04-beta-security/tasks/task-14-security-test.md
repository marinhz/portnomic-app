# Task: Application Security Audit (Penetration Testing + Code Review)

## Overview

Conduct a comprehensive security assessment of the application, combining **penetration testing** and **source code security audit**. The objective is to identify vulnerabilities, misconfigurations, and insecure coding practices that could lead to unauthorized access, data leakage, or system compromise.

The review should follow recognized security standards such as **OWASP Top 10** and common web application security best practices.

---

# Scope

## 1. Source Code Security Audit

Perform a detailed review of the application source code focusing on:

### Input Validation

- Lack of input validation
- Improper sanitization
- Injection vectors

### Authentication

- Weak authentication logic
- Password handling and hashing practices
- Token/session management
- Session fixation risks

### Authorization

- Missing role checks
- Broken access control
- Privilege escalation possibilities
- Direct object access vulnerabilities

### Data Handling

- Sensitive data exposure
- Improper encryption practices
- Logging of confidential information
- Unsafe storage of credentials

### File Handling

- Insecure file uploads
- File path manipulation
- Unrestricted file access

### API Security

- Missing authentication on endpoints
- Insufficient request validation
- Mass assignment risks
- Improper error responses exposing system details

---

# 2. Penetration Testing

Simulate real-world attack scenarios against the running application.

### Test Areas

#### Authentication & Session Management

- Brute force protection
- Session hijacking
- Token expiration and reuse

#### Authorization

- Role escalation attempts
- Access to restricted resources
- Horizontal and vertical privilege escalation

#### Injection Attacks

- SQL Injection
- Command Injection
- Template Injection

#### Client-Side Vulnerabilities

- Cross-Site Scripting (XSS)
- DOM-based XSS
- Content Security Policy weaknesses

#### Request Forgery

- Cross-Site Request Forgery (CSRF)

#### File Upload Exploitation

- Executable upload attempts
- File type bypass techniques

#### API Attacks

- Parameter manipulation
- Mass assignment
- Rate limiting bypass

#### Infrastructure Misconfiguration

- Exposed services
- Debug mode exposure
- Security headers verification

---

# Tools (Recommended but not mandatory)

Examples of tools that may be used:

- Burp Suite
- OWASP ZAP
- Nmap
- Nikto
- Dependency vulnerability scanners
- Static code analysis tools

---

# Deliverables

A detailed **Security Assessment Report** containing:

## Vulnerability List

For each issue provide:

- Vulnerability name
- Severity (Low / Medium / High / Critical)
- Description
- Affected component
- Reproduction steps
- Potential impact
- Recommended remediation

## Security Risk Summary

- Overall risk level of the application
- Critical areas requiring immediate attention

## Remediation Recommendations

- Secure coding improvements
- Configuration changes
- Infrastructure improvements

---

# Acceptance Criteria

- Full review of the application codebase
- Penetration testing executed against staging/test environment
- All discovered vulnerabilities documented
- Clear remediation guidance provided
- Security report delivered to the development team
