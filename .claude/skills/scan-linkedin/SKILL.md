---
name: scan-linkedin
description: Search LinkedIn for Java/backend job posts, evaluate each against Awais's requirements, and save qualified posts to jobs.txt. Uses Playwright MCP to browse LinkedIn directly.
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
- `DAYS_BACK` — how many days back to search (default: 1). Multiplied by 86400 for the LinkedIn datePosted param.
- `MAX_POSTS_PER_QUERY` — **target number of qualifying posts to save** per query (default: 20). Keep scrolling and reviewing until this many posts pass all filters and are saved to jobs.txt, or LinkedIn runs out of new posts to load.

If $ARGUMENTS contains a search query, override `SEARCH_QUERIES` with it.

### 1.2 Read the requirements doc
Read `personal-docs/job_requirements.md` in full. This is your evaluation guide — internalize the hard blockers, fit signals, edge cases, and output format before proceeding.

### 1.3 Read existing jobs.txt (for dedup)
Read `jobs.txt` if it exists. Collect all `Poster:` lines to build a seen-set for deduplication. A post is a duplicate if the same poster URL + role title combination already appears.

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

For each query in `SEARCH_QUERIES`, run the following loop. Track `saved_count = 0` per query.

### 3.1 Build the search URL
```
dateParam = DAYS_BACK * 86400  (e.g. 1 day = r86400, 5 days = r432000)
URL = https://www.linkedin.com/search/results/content/?keywords=[URL-encoded query]&datePosted=r[dateParam]&sortBy=date_posted
```

### 3.2 Navigate and wait for cards
1. Navigate to the search URL
2. Wait 3 seconds for the page to load
3. Check for "Feed post" cards using browser_evaluate:
   ```js
   () => Array.from(document.querySelectorAll('h2')).some(h => h.textContent.trim() === 'Feed post')
   ```
4. If no cards appear: take a screenshot to `debug-no-results.png`, log it, and move to the next query

### 3.3 Scroll loop — keep going until MAX_POSTS_PER_QUERY saved or no more posts

Repeat the following until `saved_count >= MAX_POSTS_PER_QUERY` OR 3 consecutive End keypresses load no new cards:

**a) Expand truncated posts**
```js
() => {
  document.querySelectorAll('button').forEach(btn => {
    const t = btn.textContent.trim().toLowerCase();
    if (t === '…more' || t === 'see more' || t === '… more') btn.click();
  });
}
```
Wait 1 second.

**b) Extract all post content**
```js
() => {
  function timeToSeconds(t) {
    if (!t || t === 'now' || t === 'just now') return 0;
    const m = t.match(/^(\d+)\s*([smhdw])/);
    if (!m) return 999999;
    const n = parseInt(m[1]);
    const unit = m[2];
    return n * { s: 1, m: 60, h: 3600, d: 86400, w: 604800 }[unit];
  }

  const headings = Array.from(document.querySelectorAll('h2'))
    .filter(h => h.textContent.trim() === 'Feed post');

  const posts = headings.map(h2 => {
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

    const emailMatch = postBody.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
    const email = emailMatch ? emailMatch[0] : '';

    return { authorName, authorUrl, postBody, email, timePosted, _sortKey: timeToSeconds(timePosted) };
  });

  posts.sort((a, b) => a._sortKey - b._sortKey);
  posts.forEach(p => delete p._sortKey);
  return posts;
}
```

**c) Evaluate only NEW posts** (ones not seen in previous iterations of this loop — track by authorUrl+postBody fingerprint)

For every new post, apply judgment from `job_requirements.md`:
1. Hard blockers → SKIP, log reason
2. Assess fit — Strong / Moderate / Weak
3. Check worth saving criteria
4. Check dedup against jobs.txt seen-set

If passes: append to jobs.txt immediately, increment `saved_count`, add to dedup set.

**d) Scroll down using the End key**
```
Press End key (browser_press_key with key="End")
Wait 2 seconds
```

**Important:** LinkedIn's lazy-loader is triggered by real keyboard/scroll input, NOT by `window.scrollBy`. Always use `browser_press_key` with `key="End"` — never `window.scrollBy`.

Count consecutive End presses that load zero new cards. Stop the loop after 3 such presses (LinkedIn has no more results).

Move to next query after a 3–5 second pause.

---

## Phase 4 — Save to jobs.txt

Append each qualifying post as it is found (don't batch — write immediately after evaluation):

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

## Phase 5 — Report

After all queries are done, print a summary:

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
- Dedup is based on poster URL + role title, not post text
- **Never use `window.scrollBy` for scrolling** — use `browser_press_key` with `key="End"` only
- Save each qualifying post immediately as it is found, don't wait until the end
