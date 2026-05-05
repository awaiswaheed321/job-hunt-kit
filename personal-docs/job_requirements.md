# Update this file with your own requirements before running /scan-linkedin

# Job Matching Requirements
> Used by the /scan-linkedin skill to evaluate LinkedIn posts.
> Update this file when preferences change — the skill reads it before every scan.

---

## Who We're Looking For

**Role:** [Target role title, e.g. Senior Backend Engineer / Senior Software Engineer]
**Experience:** [X+ years total (Y+ senior-level)]
**Primary stack:** [Your primary technologies, e.g. Java, Spring Boot, AWS, microservices]
**Location:** [Your city] — open to relocation; remote and hybrid both fine
**Work auth:** [Your work authorization status, e.g. OPT, H-1B, GC, citizen]

---

## Hard Blockers — Auto-Reject, Do Not Save

If a post contains any of the following, skip it entirely. Do not save to jobs.txt.

| Blocker | Examples / Signals |
|---|---|
| No sponsorship | "no sponsorship", "cannot sponsor", "will not sponsor", "unable to sponsor", "sponsorship not available/offered" |
| Citizens/GC only | "US citizens only", "citizen or GC only", "GC only", "must be authorized to work for any employer", "no visa sponsorship or transfer" |
| No H-1B / OPT / CPT | "no H-1B", "no OPT", "no CPT", "no work visa" |
| Requires 12+ years | "12+ years", "15+ years" — hard gap vs target experience. 8–10 years required is acceptable: flag the gap but do not reject. |
| Angular required | Posts where Angular is listed as **required** (not preferred). AngularJS is different — flag but don't auto-reject. |
| Active security clearance | "must hold active clearance", "TS/SCI required", "Secret clearance required" |
| Requires certifications | Mandatory cloud certifications listed as required |
| Non-US location | Role is located outside the United States. Remote roles must also be US-based. |
| C2C / 1099 / Corp-to-Corp | Any post that is C2C-only, 1099-only, or corp-to-corp-only. Only reject if C2C is the ONLY option. "C2C or W2" is acceptable — flag but do not reject. |

**Implicit blockers — also reject if clearly present:**
- "USC/GC required" or "USC/GC only" phrasing
- "No transfers" or "must be on your own visa" — means they won't sponsor
- Role is 100% frontend with no backend component
- Location is clearly outside the US with no remote/US-person option

---

## Fit Signals — Score Each Post

After ruling out hard blockers, assess fit:

### Strong Fit
- Primary stack technologies in the required skills
- Backend, distributed systems, microservices, or platform engineering focus
- Cloud services listed (AWS, GCP, Azure)
- Event-driven, reactive/non-blocking, or streaming systems
- Relational or NoSQL databases
- Messaging systems: Kafka, SQS, Kinesis, RabbitMQ
- Experience range matching your profile
- Sponsorship explicitly offered or visa types accepted
- Recruiter posts (direct contact, usually includes email)
- Remote or hybrid

### Moderate Fit
- Full-stack role with your primary backend stack
- Adjacent cloud platforms (you have primary, role wants secondary)
- Adjacent languages or frameworks you have experience in
- Slight experience mismatch (1–2 years either direction)
- Hybrid on-site in a city you would need to relocate to

### Weak Fit — Save Only If Explicitly Asked
- Frontend-heavy with your stack mentioned but secondary
- Stack is 60%+ technologies you don't have
- Very junior role
- Staff/principal level (might be overqualified mismatch OR stretch — flag it)

### Relaxed Mode (currently active)
Actively looking — apply these overrides:
- **Your stack among multiple languages** (e.g. "Java, Python, Node.js, or Go") is acceptable — save with a note
- **Experience 8–10 years** listed as required is acceptable — flag the gap, do not reject
- **Vague posts** with minimal detail are still worth saving if your primary stack is mentioned and no hard blockers are present
- **Save Moderate and borderline Weak posts** — let the user decide, don't filter aggressively

---

## What Makes a Post Worth Saving

A post is worth saving to `jobs.txt` if:
1. **No hard blockers** (above)
2. **Has a contact** — recruiter email in the post body, OR a clear call to action with DM instructions
3. **Fit is Strong or Moderate**
4. **Role is real** — not vague, has a specific role/company

If a post has Strong fit but no email — still save it (can reach out via LinkedIn DM).
If a post has Moderate fit and no email — save it with a note.
If a post has Weak fit — skip unless told otherwise.

---

## What to Extract Per Post

When saving a post, pull out:

- **Company** (if named — many recruiter posts don't name the client)
- **Role title** (exact title as stated)
- **Location + remote policy** ("Remote", "Hybrid - Chicago, IL", "On-site - Dallas, TX", etc.)
- **Experience required** (as stated)
- **Key tech stack** (required skills, bullet them)
- **Contact info** (email if present; otherwise note "DM only")
- **Sponsorship** (what exactly the post says — quote it if ambiguous)
- **Fit verdict** — Strong / Moderate / Weak
- **Flags** — anything notable: experience gap, preferred-only skills, C2C flag, etc.
- **Poster** — name and LinkedIn profile URL

---

## Output Format — jobs.txt

Append each saved post as a block:

```
---
Date:      YYYY-MM-DD
Poster:    [Name] — [LinkedIn /in/ URL]
Email:     [email or "DM only"]
Role:      [Title]
Company:   [Company name or "Unnamed client"]
Location:  [Location / Remote / Hybrid]
Fit:       Strong | Moderate | Weak
Flags:     [any flags, or "None"]

Stack:
  - [tech 1]
  - [tech 2]
  ...

Notes:
  [1-3 sentences — what stands out, gaps, why it's worth applying]

---
```

---

## Search Queries to Use

Read from `.env` at the project root → `SEARCH_QUERIES`. Default if not set:

```
java developer hiring
java spring boot hiring
senior java engineer opportunity
backend java developer
java developer OPT sponsorship
```

Time window: read `DAYS_BACK` from `.env`. Default: 1 (past 24h).
Use LinkedIn search URL: `https://www.linkedin.com/search/results/content/?keywords=[query]&datePosted=r86400&sortBy=date_posted`
(Use `r172800` for 2 days back.)

---

## Notes on Common Edge Cases

- **"Prefer local"** — not a blocker. Note the location.
- **"C2C or W2"** — acceptable. Flag it for awareness but do not reject.
- **"C2C only" / "1099 only"** — hard blocker. Reject.
- **Reposted jobs** — if the same role appears in multiple queries, dedup by role title + company. Save once.
- **Vague sponsorship** — "we may be able to support visa" or "open to discussing sponsorship" — save but add a flag noting it's ambiguous.
- **10 years listed as preferred, not required** — not a hard blocker. Flag the gap, save if otherwise strong fit.
- **Angular listed as preferred** — not a blocker. Note it as a gap.
- **Senior vs Staff** — for Staff/Principal roles, flag as potential over-requirement. Still save if primary stack matches, let the user decide.
