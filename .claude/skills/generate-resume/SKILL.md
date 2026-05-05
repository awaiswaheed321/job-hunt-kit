---
name: generate-resume
description: Generate a tailored ATS-optimized resume from a job description. Evaluates fit, builds keyword map, fills template, runs generator, and updates job tracker.
---

# generate-resume

Generate a tailored job application resume.

## Steps

1. **Read the JD** — the user has pasted it in the conversation. Extract:
   - Company name
   - Role title
   - Required skills, preferred skills, keywords, must-haves
   - Any red flags: "no sponsorship", location restrictions, experience gaps

2. **Evaluate the JD** — before doing anything else, give a quick assessment:
   - **Hard blockers** (stop and ask user before proceeding):
     - "No sponsorship" / "must be authorized for any employer" — check `personal-docs/user.json` for `needs_sponsorship`. If true, flag before proceeding.
     - Location requirement that conflicts with user's location and relocation preference
   - **Fit signal** (proceed but note):
     - Tech stack overlap: how much of the required stack does the user have?
     - Experience level match
     - Role type: backend-heavy (strong fit), full-stack (decent fit), frontend-heavy (weak fit)
     - Seniority: is the role level appropriate?
   - **Overall verdict**: Strong fit / Moderate fit / Weak fit — one line, honest

   If hard blockers exist, stop and tell the user. Otherwise continue.

3. **Read** `personal-docs/master_profile.md`

4. **Read** `tools/content.py` to discover available role functions and bullet keys.

5. **Build a keyword map**:
   - Must-match: required tools/languages/platforms — use exact JD phrasing
   - High-value: preferred or repeated terms
   - Role language: how they describe the work
   - Note anything in the JD not covered by the profile

6. **Create output folder**: `output/applied/[Company] - [Role] - [YYYY-MM-DD]/`
   Today's date is available in the system context.

7. **Copy** `tools/template.py` to that folder as `generate.py`

8. **Fill in the template**:
   - `company`, `role`, `date`, `dept`, `accent`
   - Update the import line with the correct role function names from `tools/content.py`
   - `summary`: 2-3 sentences, front-load exact job title, 3-5 hard skills from JD, one differentiator
   - `skills`: keep only rows relevant to the JD, reorder to match JD emphasis, max 6-7 rows
   - `experience`: select bullets per role following the balance rules below. Match JD emphasis.
   - `cover = None` unless the user explicitly asks for a cover letter

   **Bullet balance per role — always follow this:**
   - Most recent role: 4-6 bullets (most important — give it the most space)
   - Second-most-recent: 3-4 bullets
   - Earlier roles: 2-3 bullets each
   - Oldest role: 1-2 bullets

   **Skills section:** trim to 6-7 rows max. Only include categories relevant to the JD — drop the rest.

   sys.path: use `"..", "..", ".."` (3 levels up) since the file is inside `output/applied/Company - Role - Date/`

9. **Run** `python3 generate.py` from the project root:
   ```
   python3 "output/applied/[Company] - [Role] - [Date]/generate.py"
   ```
   Then delete generate.py:
   ```
   rm "output/applied/[Company] - [Role] - [Date]/generate.py"
   ```

10. **Re-read the generated .docx** — check:
    - Keyword coverage against JD
    - No inflated claims (check against master_profile)
    - Length: candidates with multiple distinct roles warrant 2 pages; never pad
    - No Certifications section unless the user actually has certifications
    - No Personal Projects section on senior-level resumes

11. **Update** `personal-docs/job_tracker.md` with the new entry.

12. **Report back**:
    - Path to the generated .docx
    - Keyword coverage: what matched, what was missing
    - Any flags (sponsorship, location, experience gap)
    - Anything in the JD not covered by the profile

## Rules
- Never invent experience not in master_profile.md
- No Personal Projects section on senior-level resumes
- No em dashes in bullet content
- sys.path insert must go 3 levels up for files inside output/applied/
