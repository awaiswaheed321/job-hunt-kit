---
name: scan-linkedin
description: Search LinkedIn for job posts, evaluate each against your requirements, and save qualified posts to jobs.txt. Uses Playwright MCP to browse LinkedIn directly.
argument-hint: "[optional: custom search query]"
allowed-tools: Read, Write, Bash, mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_click, mcp__playwright__browser_fill_form, mcp__playwright__browser_evaluate, mcp__playwright__browser_wait_for, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_press_key, mcp__playwright__browser_tabs
---

# /scan-linkedin

Browse LinkedIn search results, evaluate posts using Claude's judgment, and append qualified ones to `jobs.txt`.

## Arguments

User invoked with: $ARGUMENTS

- If a custom search query is in $ARGUMENTS, use it instead of the queries from `.env`.
- Otherwise read queries from `.env` → `SEARCH_QUERIES`.

---

## Phase 1 — Load Config and Requirements

### 1.1 Read `.env`
Read the file `.env` at the project root. Parse:
- `LI_EMAIL` and `LI_PASSWORD` — LinkedIn credentials
- `SEARCH_QUERIES` — comma-separated queries (fallback: "java developer hiring")
- `DAYS_BACK` — how far back to search. Supports days+hours format: `1d`, `12h`, `1d3h`, `2d12h`. Plain integers are treated as days. Converted to seconds for the LinkedIn datePosted param.
- `MAX_POSTS_PER_QUERY` — **target number of qualifying posts to save per query** (default: 20). Keep scrolling and reviewing until this many posts pass all filters and are saved to jobs.txt for that query, or LinkedIn runs out of new posts.

If $ARGUMENTS contains a search query, override `SEARCH_QUERIES` with it.

### 1.2 Read the requirements doc
Read `personal-docs/job_requirements.md` in full. This is your evaluation guide — internalize the hard blockers, fit signals, edge cases, and output format before proceeding.

### 1.3 Read existing jobs.txt (for dedup)
Read `jobs.txt` if it exists. Build two seen-sets for deduplication:
- `seen_poster_role`: collect all `Poster:` + `Role:` line pairs → a post is a duplicate if same poster URL + role title already exists
- `seen_company_role`: collect all `Company:` + `Role:` line pairs → a post is also a duplicate if same company + role title already exists (catches the same role posted by two different recruiters)

### 1.3.5 Read the no-authorized list
Read `personal-docs/no_authorized_list.md` in full. Load all company/recruiter names into memory as a blocklist. Before saving any post to jobs.txt, check the company name and poster name against this list. Partial matches count (e.g. "Devcare Columbus" matches "Devcare"). If matched, skip with reason "no-authorized list".

### 1.4 Initialize session state — resume or start fresh

State is persisted to `.playwright-mcp/scan_state.json` so the scroll loop survives context compression mid-run.

Read `.playwright-mcp/scan_state.json` if it exists (Read tool; if missing, treat as "no state").

- If the file exists and `run_started_at` is **less than 4 hours ago** → **resume**: load all fields from the file. Log "Resuming interrupted scan from state file."
- If the file exists but `run_started_at` is **4+ hours old** → **start fresh**: delete the file, initialize new state below.
- If the file does not exist → **start fresh**: initialize new state below.

**Fresh state:**
```json
{
  "run_started_at": "<ISO timestamp of now>",
  "seen_fps": [],
  "total_saved_count": 0,
  "query_saved_count": 0,
  "consecutive_empty_rounds": 0,
  "current_query_index": 0,
  "total_posts_reviewed": 0,
  "last_post_index": 0
}
```

Write this fresh state to `.playwright-mcp/scan_state.json` immediately using the Write tool.

**Field meanings:**
- `seen_fps` — fingerprints of every post evaluated this session (for within-session dedup). Capped at 2000 on every write — if it exceeds 2000 entries, trim the oldest ones.
- `total_saved_count` — cumulative saves across all queries this session (for the summary report).
- `query_saved_count` — saves for the **current query only**. Reset to 0 when advancing to the next query. This is what gets compared against `MAX_POSTS_PER_QUERY`.
- `consecutive_empty_rounds` — scroll failure counter; see Phase 3. Reset to 0 when advancing to a new query.
- `last_post_index` — how many posts were in the DOM the last time extraction ran. Used for delta extraction. Reset to 0 when advancing to a new query or navigating to a new search.
- `total_posts_reviewed` — cumulative count of unique posts evaluated (for the summary report).

A fingerprint is `(authorUrl || authorName) + '|' + postBody.slice(0, 100)`. Load `seen_fps` array into an in-memory Set at the start of each batch for fast lookup.

---

## Phase 2 — LinkedIn Login

### 2.1 Check current state
Navigate to `https://www.linkedin.com/feed` and take a snapshot. Check the page URL:
- If URL is `linkedin.com/feed` or any authenticated page → already logged in, skip to Phase 3
- If URL contains `/login`, `/authwall`, `/checkpoint` → need to log in

### 2.2 Log in
If login is needed:
1. Navigate to `https://www.linkedin.com/login`
2. Wait for the login form to appear (look for an email/username input in the snapshot)
3. Fill the form:
   ```
   #username → LI_EMAIL
   #password → LI_PASSWORD
   ```
4. Click the sign-in button (`button[type="submit"]`)
5. Wait for the page to change away from the login URL
6. Take a snapshot — confirm we're on an authenticated page (feed, mynetwork, or profile)
7. If a CAPTCHA or security challenge appears: stop and tell the user to resolve it manually in the Playwright browser window, then invoke the skill again

---

## Phase 3 — Search and Collect Posts

For each query in `SEARCH_QUERIES` (starting at `current_query_index` if resuming):

### 3.1 Build the search URL
```
Parse DAYS_BACK into total seconds:
  - "1d3h" → (1*86400) + (3*3600) = 97200
  - "12h"  → 12*3600 = 43200
  - "2d"   → 2*86400 = 172800
  - plain integer (e.g. "1") → treated as days → 1*86400 = 86400
dateParam = total seconds computed above
URL = https://www.linkedin.com/search/results/content/?keywords=[URL-encoded query]&sortBy=%22date_posted%22&datePosted=%22r[dateParam]%22
```

Note: the `%22` quotes around values are required — LinkedIn ignores the filters without them.

### 3.2 Navigate and wait for cards
1. Navigate to the search URL
2. Wait 3 seconds for the page to load
3. Check for "Feed post" cards using browser_evaluate:
   ```js
   () => Array.from(document.querySelectorAll('h2')).some(h => h.textContent.trim() === 'Feed post')
   ```
4. If no cards appear: take a screenshot to `.playwright-mcp/debug-no-results.png`, log it, and move to the next query

### 3.3 Scroll loop — keep going until `query_saved_count >= MAX_POSTS_PER_QUERY` or no more posts

> **CRITICAL — past execution failure:** Do NOT run the outer loop only once. After each extract+evaluate pass, check `query_saved_count` against `MAX_POSTS_PER_QUERY`. If the target is not met and LinkedIn still has more posts, scroll another batch and repeat. With a ~5–10% qualification rate, hitting MAX_POSTS_PER_QUERY=50 requires loading ~500–1000 raw posts across many batches. Never stop scrolling just because you've loaded and evaluated one batch.

Repeat the following until `query_saved_count >= MAX_POSTS_PER_QUERY` OR `consecutive_empty_rounds >= 6`:

**a) Record pre-scroll post count**

```js
() => {
  const h2s = Array.from(document.querySelectorAll('h2')).filter(h => h.textContent.trim() === 'Feed post');
  return h2s.length;
}
```
Store as `post_count_before`.

**b) Scroll to load more posts — with early exit**

LinkedIn's content lives in `<main id="workspace">` (overflow-y: auto), not the document body. Only scrolling `main.scrollTop` triggers the lazy-loader. Never use `window.scrollBy` or `browser_press_key("End")` — they target the document body and do nothing.

Run up to 5 scroll iterations. After each scroll, wait **3 seconds**, then check the count. If the count has not changed for **2 consecutive scrolls within this batch**, stop scrolling early — LinkedIn has paused loading.

```js
// Each scroll iteration:
() => {
  const main = document.getElementById('workspace');
  main.scrollTop = main.scrollHeight;
  const h2s = Array.from(document.querySelectorAll('h2')).filter(h => h.textContent.trim() === 'Feed post');
  return { postCount: h2s.length, scrollTop: main.scrollTop, scrollHeight: main.scrollHeight };
}
```

Record final `post_count_after` (last non-repeating count, or last count if all repeated).

Then expand truncated posts once:
```js
() => {
  document.querySelectorAll('button').forEach(btn => {
    const t = btn.textContent.trim().toLowerCase();
    if (t === '…more' || t === 'see more' || t === '… more') btn.click();
  });
}
```
Wait 1 second.

**c) Update `consecutive_empty_rounds`**

```
if post_count_after > post_count_before:
    consecutive_empty_rounds = 0   # LinkedIn loaded new posts
else:
    consecutive_empty_rounds += 1  # LinkedIn loaded nothing new
```

This is the ONLY correct signal for "LinkedIn is exhausted." A batch where posts loaded but were all blockers/duplicates must NOT increment this counter — those were real results, just not qualifying ones.

**d) Delta extraction — only new posts**

Read `last_post_index` from current state.

Run `browser_evaluate` with this function, substituting the actual numeric value of `last_post_index` in place of `LAST_POST_INDEX`:

```js
() => {
  const allHeadings = Array.from(document.querySelectorAll('h2'))
    .filter(h => h.textContent.trim() === 'Feed post');
  const headings = allHeadings.slice(LAST_POST_INDEX); // only posts not yet seen

  return headings.map(h2 => {
    const container = h2.parentElement;
    const rawText = container.textContent.trim().replace(/^Feed post\s*/, '');

    const followIdx = rawText.indexOf('• Follow');
    const postBody = followIdx !== -1
      ? rawText.slice(followIdx + 8).trim()
      : rawText;

    const authorLink = Array.from(container.querySelectorAll('a[href*="/in/"]'))
      .find(a => a.textContent.trim());
    const authorUrl = authorLink ? authorLink.href.split('?')[0] : '';

    const authorName = rawText.split(/[•\n]/)[0].trim().replace(/\s{2,}.*/, '');

    const header = followIdx !== -1 ? rawText.slice(0, followIdx) : '';
    const timeMatch = header.match(/\b(now|just now|\d+\s*[smhdw])\b/i);
    const timePosted = timeMatch ? timeMatch[1].trim() : '';

    const emailMatch = postBody.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?=[^a-zA-Z0-9._+-]|$)/);
    const email = emailMatch ? emailMatch[0] : '';

    const fp = (authorUrl || authorName) + '|' + postBody.slice(0, 100);

    return { authorName, authorUrl, postBody: postBody.slice(0, 3000), email, timePosted, fp };
  });
}
```

Save to `.playwright-mcp/posts-raw.json` (use the `filename` parameter). Then read the file with the Read tool — it now contains only the new posts from this batch (typically 10–40 entries, readable in one call).

After reading: update `last_post_index` in state to `last_post_index + number_of_new_posts_extracted` (i.e., `post_count_after`).

**e) Identify and evaluate NEW posts only**

For each post in the extracted list:
1. Compute `fp = (authorUrl || authorName) + '|' + postBody.slice(0, 100)`
2. If `fp` is already in `seen_fps` → skip silently (timestamp-shifted duplicate)
3. Add `fp` to `seen_fps`
4. **Evaluate** against `job_requirements.md`:
   - Hard blockers → log one-liner: `SKIP [AuthorName]: <reason>` (e.g., `SKIP Anisha K: No OPT + Lead role`)
   - Weak fit → log one-liner: `SKIP [AuthorName]: weak fit (<reason>)`
   - No-authorized list match → log one-liner: `SKIP [AuthorName]: no-authorized list`
   - Duplicate → log one-liner: `SKIP [AuthorName]: duplicate`
   - Qualifying → save to jobs.txt immediately (see Phase 4), increment `query_saved_count` and `total_saved_count`, add poster+role to dedup sets, log: `SAVE [AuthorName]: <Role> @ <Company> — <Fit>`
5. Increment `total_posts_reviewed` for every post with a new fingerprint, regardless of outcome

**f) Persist state to disk after every batch**

```json
{
  "run_started_at": "<original ISO timestamp — do not update>",
  "seen_fps": ["<all fps seen so far, capped at 2000 — trim oldest if over>"],
  "total_saved_count": <cumulative saves across all queries>,
  "query_saved_count": <saves for the current query only>,
  "consecutive_empty_rounds": <current value>,
  "current_query_index": <current query index>,
  "total_posts_reviewed": <current value>,
  "last_post_index": <updated value>
}
```

This write must happen after every batch. It is what allows the loop to survive context compression.

Stop the loop when `consecutive_empty_rounds >= 6` OR `query_saved_count >= MAX_POSTS_PER_QUERY`.

**Advancing to next query:** pause 3–5 seconds, then reset `consecutive_empty_rounds = 0`, `query_saved_count = 0`, `last_post_index = 0`, increment `current_query_index`. Write updated state to disk.

---

## Phase 4 — Save to jobs.txt

Append each qualifying post as it is found (write immediately, not in batches):

```
---
Date:      YYYY-MM-DD
Poster:    [authorName] — [authorUrl]
Email:     [email or "DM only"]
Role:      [role title extracted from post, or "Not specified"]
Company:   [company name if mentioned, or "Unnamed client"]
Location:  [location and remote policy]
Fit:       Strong | Moderate | Weak
Flags:     [flags or "None"]

Stack:
  - [tech 1]
  - [tech 2]

Notes:
  [1-3 sentences: what stands out, any gaps, why worth applying]

---
```

Today's date is in the system context — use it for the `Date:` field.

---

## Phase 5 — Cleanup and Report

After all queries are done, delete the state file:
```bash
rm -f .playwright-mcp/scan_state.json
```

Print a summary:

```
Scan complete.
Queries run:               [N]
Posts reviewed:            [N]
Saved to jobs.txt:         [N]
  - Strong fit:            [N]
  - Moderate fit:          [N]
Skipped (hard blockers):   [N]
Skipped (weak fit):        [N]
Skipped (duplicate):       [N]
LinkedIn exhausted early:  yes/no (hit end of results before reaching MAX_POSTS_PER_QUERY)
```

Then list saved posts:
```
Saved posts:
  1. [authorName] — [Role] @ [Company] ([Fit]) — [email or "DM only"]
  2. ...
```

If nothing was saved: say so clearly and suggest adjusting search queries or DAYS_BACK.

---

## Rules

- Never invent content — only save what's actually in the post
- Never mark a post "Strong fit" if it has an unresolved hard blocker
- Ambiguous sponsorship language ("may support") → save with a flag, not skip
- If LinkedIn shows a security challenge mid-scan: pause, tell the user, stop the skill
- Do not close the Playwright browser between queries — reuse the session
- Dedup against jobs.txt is based on poster URL + role title
- Session dedup uses fingerprints (`authorUrl|postBody[:100]`) — never re-evaluate a post already seen this session
- **Never use `window.scrollBy` or `browser_press_key("End")` for scrolling** — both target the document body (~855px, never scrolls). Always use `document.getElementById('workspace').scrollTop = main.scrollHeight` via `browser_evaluate`
- **Always use the `filename` parameter** when calling `browser_evaluate` for post extraction
- **Delta extraction**: always substitute the current `last_post_index` value into the extraction JS. A value of 0 extracts all posts (correct for first batch of a query). Reset `last_post_index` to 0 when navigating to a new query.
- **`consecutive_empty_rounds` tracks scroll failures only** — increment only when `post_count_after == post_count_before`. A batch where posts loaded but were all blockers/duplicates must NOT increment this counter.
- **`query_saved_count` resets per query** — it is the counter compared against `MAX_POSTS_PER_QUERY`. `total_saved_count` accumulates across all queries and is used only for the final report.
- **`seen_fps` cap**: trim to last 2000 entries on every state write to prevent unbounded growth.
- **State file is session-scoped** — `run_started_at` < 4 hours = resume; ≥ 4 hours = start fresh automatically.
- **Write state to disk after every batch** — never rely solely on in-context memory.
- **Evaluation output**: one-liner for skips (`SKIP [Name]: reason`), full format only for saves. Do not write verbose reasoning for every skip.
- **Early scroll exit within a batch**: stop scrolling if the post count fails to increase for 2 consecutive scrolls within the same batch. This saves ~6–9 seconds when LinkedIn is near-exhausted.
- Save each qualifying post immediately as it is found, don't wait until the end
- Email regex must use the strict terminator form: `(?=[^a-zA-Z0-9._+-]|$)`
