---
name: setup
description: First-time setup for the job application system. Collects user profile, work experience, and Gmail credentials, then generates master_profile.md, content.py, user.json, and job_tracker.md. Run this once before using /generate-resume, /apply, or /send-email.
---

# setup

Welcome to the job application system. This is a one-time setup that configures everything needed to generate tailored resumes and send applications.

**Have ready:** your resume or CV (text you can paste or a file path), and your Gmail address + App Password if you want email sending enabled.

**Re-run check:** Before doing anything else, check if `personal-docs/user.json` already exists. If it does, ask:
> "Setup has already been run. Re-running will overwrite your existing profile, master_profile.md, content.py, and job_tracker.md. Continue? (yes / no)"
If no, stop and remind them to use `/generate-resume`, `/apply`, or `/send-email`.

---

## Phase 1 — Basic Contact Info

Ask the user for all of the following at once:

```
Please provide your basic info:
1. Full name (as it should appear on your resume — e.g. "Jane Smith")
2. Professional email address
3. Phone number with country code (e.g. +1-555-123-4567)
4. LinkedIn URL (e.g. linkedin.com/in/yourname)
5. Portfolio or personal website URL (or "none")
6. GitHub URL (or "none" — note: GitHub is not included on resumes by default unless your profile has notable public work)
7. Current city and state/country (e.g. "Austin, TX" or "London, UK")
8. Open to relocation? (yes / no / remote only)
```

Wait for their answer before continuing.

---

## Phase 2 — Work Authorization

Ask:

```
Work authorization:
1. What is your current work status?
   a) US Citizen or Permanent Resident
   b) Work visa (H-1B, L-1, TN, O-1, etc.) — specify type
   c) OPT / CPT / EAD — specify type and expiry date
   d) Not yet authorized / applying for authorization
   e) Working in another country — describe briefly

2. Do you need employer sponsorship now or in the future? (yes / no / only for long-term visa extension)

3. What should your application say about work authorization?
   Examples: "Authorized to work in the US" | "US Citizen, no sponsorship needed" | "On OPT, will need H-1B sponsorship"
```

From their answers, compose two strings:
- `work_auth_statement` — short phrase for resume forms (e.g. "Authorized to work in the US")
- `work_auth_para` — 1-2 sentences for cover letters (e.g. "I am on STEM OPT through June 2027 and will need H-1B sponsorship for long-term employment.")

---

## Phase 3 — Education

Ask:

```
List your degrees, most recent first. For each degree:
- Degree type (BS, MS, PhD, Diploma, etc.)
- Field of study
- Institution name
- City and country
- Graduation year — or "Expected [Month Year]" if still in progress

Also: any professional certifications (AWS Certified, PMP, CPA, etc.)? List them or say "none".

Say "done" when finished.
```

Collect all degrees and certifications. Store certifications separately — they go into `master_profile.md` and `user.json` as `"certifications": [...]` (empty array if none). This controls whether a Certifications section appears on resumes.

Wait for "done" before moving on.

---

## Phase 4 — Work Experience

This is the most important phase — it generates the bullet library that powers every resume.

First, ask the user to choose an input method:

```
For your work experience, choose one:
  a) Paste your full resume or CV text — I'll extract all roles from it
  b) Describe each role one at a time — I'll ask questions for each
  c) Provide a file path to your resume (PDF or text file) — I'll read it

Which do you prefer?
```

### If they paste CV text or a file path:
Read the content. Extract for each role:
- Company name
- Job title
- Start and end dates (e.g. "Jan 2022 – Present")
- Location and work type (on-site / remote / hybrid)
- All key achievements and responsibilities

Ask the user to confirm you've captured everything correctly, or add anything missing.

### If they go role by role:
For each role, ask:

```
Role [N]:
1. Company name (if you were a contractor/consultant embedded at a client, give both: "ContractCo (Client: BigCo)")
2. Job title
3. Start and end date (e.g. "Jan 2022 – Present" or "Jan 2020 – Dec 2021")
4. Location (city, state/country) and work type (on-site / remote / hybrid)
5. Describe 3-6 key achievements or projects. Be specific:
   - What did you build, fix, or improve?
   - What was the scale or impact (users, volume, performance, cost)?
   - Any relevant numbers (before/after metrics, team size, deployment scope)?

Type "next" when done with this role, "done" when finished all roles.
```

### After collecting all roles — convert to professional bullets:

For each role, write **ATS-optimized resume bullets** following these rules:

**Bullet formula:** `[Strong action verb] + [what you did / built / solved] + [result / metric / scope]`

**Action verbs:** Built / Engineered / Developed / Implemented / Designed / Scaled / Optimized / Reduced / Eliminated / Improved / Led / Drove / Diagnosed / Resolved / Migrated / Integrated / Deployed / Automated

**When there are no numbers:** end with a concrete functional outcome (what it enabled or what problem it eliminated), or use scope/scale as the weight-carrier. Never pad with vague adjectives like "significantly improving" or "greatly enhancing" — drop the trailing clause if there's nothing concrete to say.

**Tense:** current role = present tense ("Owns", "Processes"). Past roles = past tense ("Built", "Resolved").

**ATS rules:** no em dashes, no hyphens in bullet text — use commas or colons instead.

Generate **4-8 bullet keys for the most recent role**, **3-5 for older roles**, **1-3 for the oldest**. Name each key with a short descriptive slug (e.g. "pipeline", "auth_system", "api_integration", "db_crisis").

---

## Phase 5 — Gmail Setup (Optional)

Ask:

```
Do you want to configure Gmail so Claude can send application emails directly? (yes / no)
```

If yes:

```
1. Gmail address you'll send from:
2. Gmail App Password — to generate one:
   Go to myaccount.google.com → Security → 2-Step Verification → App Passwords
   Create one named "Mail" and paste the 16-character code here.
```

If no, skip and note that .env will need to be created manually before /apply or /send-email will work.

---

## Phase 6 — Generate Everything

After collecting all information, generate the following files. Tell the user what you're creating at each step.

### 6.1 Create personal-docs/ directory

```bash
mkdir -p personal-docs
```

### 6.2 Create personal-docs/user.json

Build a JSON file with the collected info:

```json
{
  "name": "<full name>",
  "email": "<professional email>",
  "phone": "<phone with country code>",
  "linkedin": "<linkedin url>",
  "portfolio": "<portfolio url or empty string>",
  "github": "<github url or empty string>",
  "location": "<city, state/country>",
  "relocation_open": <true or false>,
  "contact_line": "<phone>  |  <email>  |  <linkedin>  |  <portfolio if present>  |  <location>",
  "work_auth_statement": "<short phrase for resume forms>",
  "needs_sponsorship": <true or false>,
  "work_auth_para": "<1-2 sentences for cover letters>",
  "linkedin_para": "My LinkedIn profile (<linkedin url>) is current and reflects my current role.",
  "education": [
    {
      "degree": "<degree type, field of study>",
      "institution": "<institution name>",
      "location": "<city, country>",
      "year": "<year or Expected Month Year>"
    }
  ],
  "certifications": []
}
```

**contact_line format:** include phone, email, LinkedIn, and portfolio (if provided). Add location at the end. Omit portfolio if "none". Separate each item with `  |  ` (two spaces, pipe, two spaces).

Write this to `personal-docs/user.json`.

### 6.3 Create personal-docs/master_profile.md

This is the comprehensive experience document Claude reads when generating every resume. Structure it as:

```markdown
# [Name] — Master Profile

Last updated: [today's date]

## Identity & Contact

- **Name:** [name]
- **Email:** [email]
- **Phone:** [phone]
- **LinkedIn:** [linkedin]
- **Portfolio:** [portfolio or N/A]
- **GitHub:** [github or N/A]
- **Location:** [location] ([relocation status])

## Work Authorization

[Full details of work status, sponsorship situation, timeline if applicable. Be specific — this is what Claude reads to answer sponsorship questions accurately.]

## Professional Experience

### [Company] — [Title] | [Dates] | [Location]

[All achievements in detail, including all context the user provided: what was built, the problem it solved, the scale, the tech stack, any relevant numbers. This is the source of truth — be thorough, not concise. Every important detail from the user's descriptions should appear here.]

[Repeat for each role, most recent first]

## Education

[All degrees, most recent first: degree, institution, location, year/status]

## Technical Skills

[All technologies, languages, tools, and frameworks — grouped by category. Extract from experience descriptions plus anything user explicitly mentioned.]

## Notes for Resume Generation

[Any special instructions — NDAs, things never to say, how to describe employment gaps, contractor relationships, client names that are confidential, etc. If any role has an NDA or confidentiality constraint, note it here.]
```

Be thorough — this document is read in full every time a resume is generated. Include every detail the user provided.

### 6.4 Generate tools/content.py

Write a complete Python file that provides the bullet library. Structure:

```python
"""
Experience bullet library — generated by /setup on [date].
Single source of truth for resume bullets.

Usage in a job script:
    from tools.content import role_companyslug1, role_companyslug2, ...

    experience = [
        role_companyslug1(["key1", "key2", "key3"]),
        role_companyslug2(["key1"]),
    ]

Keys let you select which bullets to include per role. Order is preserved.
Read this file to see all available keys for each role before filling template.py.

Available roles and keys:
  role_[slug1] — [Company Name]: [list all keys with one-line description each]
  role_[slug2] — [Company Name]: [list all keys]
  ...
"""


def _pick(library, keys):
    return [library[k] for k in (keys or library)]


# ── [Company Name] bullet library ─────────────────────────────────────────────

_B_[slug1] = {
    "key1": (
        "Bullet text..."
    ),
    "key2": (
        "Bullet text..."
    ),
}

# [Repeat for each role]


def role_[slug1](keys=None):
    """keys: subset of key1, key2, ..."""
    return {
        "company":  "[Company Name]",
        "title":    "[Job Title]",
        "dates":    "[Start – End]",
        "location": "[City, ST (on-site/remote/hybrid)]",
        "bullets":  _pick(_B_[slug1], keys),
    }

# [Repeat for each role]
```

**Company name slug rules:** lowercase, letters and numbers only, underscores for spaces. Examples: "Google LLC" → `google`, "JP Morgan Chase" → `jpmorgan`, "ContractCo (Client: BigCorp)" → `bigcorp` (use the client name when embedded at a client).

**Bullet quality rules:**
- Write the bullets exactly as they would appear on the resume — professional, polished, final copy
- Follow the formula: action verb + what + result/outcome
- No em dashes, no hyphens — use commas or colons
- Current role: present tense. Past roles: past tense.
- If a bullet has no concrete outcome, let the verb + context carry it — no vague padding

After writing content.py, also **update tools/template.py**:
1. Replace the commented import placeholder with actual imports for the generated function names
2. Update the experience section comment to list the available role functions and their keys (copy from the content.py docstring)

### 6.5 Create personal-docs/job_tracker.md

```markdown
# Job Application Tracker

| Date | Company | Role | Status | Resume File | Sponsorship | Notes |
|------|---------|------|--------|-------------|-------------|-------|
```

### 6.6 Create .env (if Gmail setup was done)

```
GMAIL_USER=<gmail address>
GMAIL_APP_PASSWORD=<app password>
```

Write to `.env` at the project root.

---

## Phase 7 — Confirm Setup

Print a completion summary:

```
Setup complete.

✓ personal-docs/master_profile.md — your full experience profile ([N] roles)
✓ personal-docs/job_tracker.md   — empty tracker, ready to fill
✓ personal-docs/user.json        — contact info and config (gitignored)
✓ tools/content.py               — bullet library ([N] roles, [M] total bullets)
✓ tools/template.py              — updated with your role function imports
[✓ .env                          — Gmail configured for sending] (if applicable)

You're ready. Use:
  /generate-resume  — paste a JD to get a tailored .docx resume
  /apply            — generate resume + write and send application email
  /send-email <to>  — send an existing resume to a recruiter
```

---

## Rules

- Never invent experience not provided by the user
- If descriptions are vague, ask clarifying questions before writing bullets — better to ask once than generate weak bullets
- Always write bullets in correct tense (current = present, past = past)
- No em dashes or hyphens in any bullet or email content — use commas or colons
- If a role has an NDA or confidential client, note it clearly in master_profile.md and never name the client in any output
- Do not add certifications if the user has none
