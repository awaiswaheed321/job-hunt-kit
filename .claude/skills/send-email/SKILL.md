---
name: send-email
description: Send a job application email via Gmail with resume attached. Use when the user says "send email", "send application", "/send-email", or wants to email a recruiter.
disable-model-invocation: true
argument-hint: <to> [subject] [resume-path]
allowed-tools: Read, Glob, Bash, mcp__claude_ai_Gmail__authenticate, mcp__claude_ai_Gmail__complete_authentication, mcp__claude_ai_Gmail__send_email, mcp__claude_ai_Gmail__list_labels
---

# Send Job Application Email

Send a job application email with resume attached via Gmail.

## Arguments

User invoked this with: $ARGUMENTS

Parse arguments in order:
1. `<to>` — recipient email address (required)
2. `[subject]` — email subject line (optional — infer from context if not given)
3. `[resume-path]` — path to .docx resume file (optional — search if not given)

## Steps

### 1. Parse inputs

Extract `to`, `subject`, and `resume-path` from $ARGUMENTS.

If `subject` is not provided:
- Read `personal-docs/user.json` to get the user's name
- Check if there's an active output folder (e.g. `output/applied/Company - Role - Date/`) and derive subject like: `Application: Senior Backend Engineer — [Name]`
- Otherwise ask the user for the subject before proceeding

If `resume-path` is not provided:
- Use Glob to search `output/applied/**/*.docx` — pick the most recently modified resume file
- If multiple candidates exist, list them and ask the user which one to attach
- If none found, ask the user to provide the path

### 2. Read email body

Look for an email file in the same folder as the resume:
- Glob for `email_*.docx` or `email_*.md` or `email_*.txt` in the same directory
- If a text/markdown file is found, Read it and use its content as the email body
- If only a .docx exists, note to the user that you'll use it as-is but can't read it — ask if they want to paste the body instead
- If no email file exists, compose a short email body using the Application Email rules from CLAUDE.md (who you are, work auth, attach resume, available for call)

### 3. Authenticate Gmail

Call `mcp__claude_ai_Gmail__authenticate` to check/start the OAuth flow.

If authentication is needed:
- Share the authorization URL with the user
- Wait for them to complete it and paste back the callback URL
- Call `mcp__claude_ai_Gmail__complete_authentication` with the callback URL
- Confirm authentication succeeded before proceeding

### 4. Send the email

Call the Gmail send tool with:
- `to`: the recipient address
- `subject`: the subject line
- `body`: the email body text
- `attachments`: the resume .docx file path

After sending, confirm success to the user and print:
- To: `<address>`
- Subject: `<subject>`
- Resume attached: `<filename>`

### 5. Log it

Remind the user to update `personal-docs/job_tracker.md` with the application status if not already done.
