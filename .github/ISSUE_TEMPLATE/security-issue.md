---
name: Security Issue
about: Report a security vulnerability or concern
title: '[SECURITY] [Brief Description]'
labels: 'security, bug'
assignees: ''
---

⚠️ **SECURITY NOTICE**
**Please do not include sensitive information, credentials, or exploitation details in this public issue.**

## Security Concern Type
- [ ] **Critical** - Active vulnerability that could compromise user funds/data
- [ ] **High** - Security weakness that could lead to data exposure
- [ ] **Medium** - Security improvement or hardening opportunity  
- [ ] **Low** - Security best practice or policy issue

## Affected Components
<!-- Which parts of the system are affected? -->
- [ ] Trading Journal (user input processing)
- [ ] Technical Indicators (market data handling)
- [ ] User Authentication (login/session management)
- [ ] Database Access (Supabase integration)
- [ ] API Integration (external service calls)
- [ ] Security Scanner (input validation)
- [ ] Other: [specify]

## Impact Assessment
**Potential Impact:**
- [ ] User data exposure
- [ ] Unauthorized access
- [ ] API credential compromise
- [ ] Prompt injection vulnerability
- [ ] SQL injection risk
- [ ] Cross-site scripting (XSS)
- [ ] Cross-site request forgery (CSRF)
- [ ] Other: [specify]

**Attack Vector:**
- [ ] User input (journal entries, parameters)
- [ ] API endpoints
- [ ] Authentication flow
- [ ] Database queries
- [ ] External integrations
- [ ] Other: [specify]

## Brief Description
<!-- High-level description without sensitive details -->
[Describe the security concern in general terms]

## Affected Users
- [ ] All users
- [ ] Authenticated users only
- [ ] Admin users only
- [ ] Specific user types: [specify]

## Reproduction Information
**Can this be reproduced?**
- [ ] Yes, consistently
- [ ] Yes, intermittently  
- [ ] Theoretical risk only
- [ ] Unknown

**Environment:**
- [ ] Development
- [ ] Staging
- [ ] Production
- [ ] All environments

## Recommended Actions
<!-- What should be done to address this? -->
- **Immediate:** [Urgent steps to mitigate risk]
- **Short-term:** [Fixes to implement soon]
- **Long-term:** [Architectural improvements]

## Reporter Contact
**For sensitive details or proof-of-concept:**
- **Email:** [Your secure email for private communication]
- **Preferred Contact Method:** [Signal, encrypted email, etc.]

## Related Issues
<!-- Link to related security issues or improvements -->
- Related: #[issue-number]

---

## For FortunaMind Security Team

**Triage Information (Internal Use):**
- **CVSS Score:** [To be assigned]
- **Severity:** [To be confirmed]
- **Priority:** [To be assigned]
- **Assigned To:** [Security team member]
- **Target Resolution:** [Date]

**Response Checklist:**
- [ ] Initial assessment completed
- [ ] Risk level confirmed
- [ ] Stakeholders notified
- [ ] Fix prioritized
- [ ] Testing plan created
- [ ] Communication plan prepared (if public disclosure needed)

**Security Review:**
- [ ] Code review completed
- [ ] Penetration testing performed
- [ ] Fix verified
- [ ] Documentation updated
- [ ] Monitoring enhanced (if applicable)

---

**Note:** This issue will be made private if it contains exploitable vulnerability details. Please use secure communication channels for sensitive information.