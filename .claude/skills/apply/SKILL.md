---
name: apply
description: Full job application workflow — generate tailored resume, write application email, and send via Gmail. Use when user pastes a job posting and says "apply", "send application", "/apply", or "generate and send".
disable-model-invocation: true
argument-hint: [recruiter-email]
allowed-tools: Read, Write, Edit, Glob, Bash
---

# Full Job Application

End-to-end workflow: resume generation → email writing → Gmail send.

## Arguments

User invoked with: $ARGUMENTS

- If a recruiter email address is in $ARGUMENTS, capture it now.
- If not provided, ask for it before the send step (not now — don't block generation).

---

## Phase 1 — Evaluate the JD

### 1.1 Read requirements and tracker
Read `personal-docs/job_requirements.md` — use its hard blockers, fit signals, and edge case rules as the evaluation guide. This is the single source of truth; do not rely on memory of the rules.

Read `personal-docs/job_tracker.md` — check if this company + role combination has already been applied to. If an entry exists with status "Applied", stop and tell the user: "Already applied to [Role] at [Company] on [date]. Apply again?" Do not proceed unless the user confirms.

Read `personal-docs/user.json` for `needs_sponsorship` and `relocation_open`.

### 1.2 Extract JD details
Read the job description from the conversation. Extract:
- Company name, role title
- Required and preferred skills, tech stack, keywords
- Location, remote policy, sponsorship language
- Recruiter email (if present in the post)

### 1.3 Apply hard blockers
Use the hard blockers defined in `personal-docs/job_requirements.md`. At minimum:
- "No sponsorship" / "must be authorized to work for any employer" — if `needs_sponsorship` is true in user.json, stop and flag before proceeding.

**Location:** If `relocation_open` is true in user.json, proceed for location-specific roles and note the situation in the email. If false, flag if the role requires relocation.

### 1.4 Fit verdict
Output a one-line verdict: **Strong fit / Moderate fit / Weak fit** — then continue regardless of fit level.

---

## Phase 2 — Generate Resume

### 2.1 Read profile and config
Read `personal-docs/master_profile.md` and `personal-docs/user.json`.

### 2.2 Read content.py and build keyword map
Read `tools/content.py` to discover available role functions and bullet keys.

Build keyword map:
- Must-match: required tools/languages/platforms — use exact JD phrasing
- High-value: preferred or repeated terms
- Role language: how they describe the work
- Note any JD requirements not covered by the profile

### 2.3 Create output folder
```
output/applied/[Company] - [Role] - [YYYY-MM-DD]/
```
Use today's date from system context.

### 2.4 Copy and fill template
Copy `tools/template.py` into that folder as `generate.py`. Fill in:
- `company`, `role`, `date`, `dept`, `accent`
- Update the import line with correct role function names from `tools/content.py`
- `summary`: 2-3 sentences — front-load exact job title, 3-5 hard skills from JD, one differentiator
- `skills`: keep only rows relevant to the JD, reorder to match JD emphasis, max 6-7 rows
- `experience`: select bullets per role following the balance rules

**Bullet balance (always follow):**
- Most recent role: 4-6 bullets (most important — give it the most space)
- Second-most-recent: 3-4 bullets
- Earlier roles: 2-3 bullets each
- Oldest role: 1-2 bullets

`cover = None` unless user explicitly asked for a cover letter.

**sys.path insert:** use `"..", "..", ".."` (3 levels up from `output/applied/Company - Role - Date/`).

### 2.5 Run generator and clean up
```bash
python3 "output/applied/[Company] - [Role] - [Date]/generate.py"
rm "output/applied/[Company] - [Role] - [Date]/generate.py"
```
Run from the project root.

### 2.6 Verify output
Confirm the .docx was created. Check:
- Keyword coverage vs JD
- No inflated claims vs master_profile
- Length: candidates with multiple distinct roles warrant 2 pages; never pad
- No Certifications section unless user has certifications
- No Personal Projects section on senior-level resumes
- No em dashes in bullet content

---

## Phase 3 — Write Email

Read `personal-docs/user.json` for contact info (`name`, `phone`, `email`, `linkedin`, `portfolio`, `work_auth_para`).

Write the application email body:

**Structure (2-3 paragraphs):**
1. **Who you are + proof points** — current role, 1-2 strongest credentials with real numbers tied to the JD, direct relevance.
2. **Gaps / honest notes** — only if there's a meaningful stack gap or location situation. Skip if nothing to flag.
3. **Work auth + close** — use `work_auth_para` from user.json. End with: "Resume attached — happy to connect."

**Signature block (always include, values from user.json):**
```
Best regards,
[name]
[phone]
[email]
[linkedin]
[portfolio — if present]
```

**Tone rules:**
- Confident, direct — write like a senior engineer, not a job seeker
- No "I am excited to apply", "I believe I would be a great fit", "Thank you for your consideration"
- No em dashes, no hyphens in email prose — use commas, colons, or restructure
- 150-250 words total

**Subject line format:** `Application: [Role Title] — [Name]`

Show the email subject and body to the user for review before sending.

---

## Phase 4 — Send via Gmail SMTP

### 4.1 Get recruiter email
If captured from $ARGUMENTS or from the JD, use it. If not provided and not in the JD, ask now: "What's the recruiter's email address?"

If the job is marked "DM only" and no email exists anywhere: skip Phase 4 entirely. Tell the user: "No email found — resume generated. Send via LinkedIn DM to [posterName]." Then go to Phase 5.

### 4.2 Send via Python SMTP

Write a Python script to `/tmp/send_app.py` and run it. Use the actual values for `to_email`, `subject_line`, `email_body`, and `resume_path`:

```python
import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Read .env — run from project root so ".env" resolves correctly
env = {}
with open(".env") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

user     = env["GMAIL_USER"]
password = env["GMAIL_APP_PASSWORD"]

to_email    = "FILL"   # recruiter address
subject_line = "FILL"  # e.g. Application: Senior Engineer — Jane Smith
email_body   = """FILL"""  # the full email body text
resume_path  = "FILL"  # e.g. output/applied/Company - Role - Date/JaneSmith_Company.docx

# Build message
msg = MIMEMultipart()
msg["From"]    = user
msg["To"]      = to_email
msg["Subject"] = subject_line
msg.attach(MIMEText(email_body, "plain"))

# Attach resume
with open(resume_path, "rb") as f:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(f.read())
encoders.encode_base64(part)
part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(resume_path)}"')
msg.attach(part)

# Send
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(user, password)
    server.sendmail(user, to_email, msg.as_string())
    print(f"Sent to {to_email}")
```

If `.env` is missing or credentials fail, tell the user — do not silently skip the send.

### 4.3 Confirm
Print send summary:
```
Sent to:   <email>
Subject:   <subject>
Attached:  [Name]_[Company].docx
```

---

## Phase 5 — Update Tracker

Update `personal-docs/job_tracker.md` with a new entry:
- Company, role, date applied, resume file path, status: Applied
- Note if any flags (sponsorship risk, stack gaps)

---

## Rules (never break)
- Never invent experience not in master_profile.md
- No Certifications section unless user has actual certifications
- No Personal Projects section on senior-level resumes
- No em dashes anywhere in output docs or emails
- Flag "no sponsorship" roles — do not silently proceed
