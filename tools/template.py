"""
COPY THIS FILE to output/applied/[Company] - [Role] - [YYYY-MM-DD]/generate.py
then fill in every FILL section below.

Read tools/content.py to discover available role functions and bullet keys.
Run /setup first if content.py has no role functions yet.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from tools.runner import generate
# FILL: import your role functions — check tools/content.py for available function names
# from tools.content import role_company1, role_company2, role_company3

generate(
    company = "FILL",                   # e.g. "Google"
    role    = "FILL",                   # e.g. "Software Engineer"
    date    = "FILL",                   # e.g. "March 24, 2026"
    dept    = "FILL",                   # team/dept shown in cover letter salutation
    accent  = (68, 114, 196),           # brand color RGB — change per company

    summary = (
        "FILL"
        # 2-3 sentences. Front-load exact job title. 3-5 hard skills from JD. One differentiator.
    ),

    skills = [
        # Trim to 6-7 rows max. Only include categories the JD actually calls for.
        ("Languages",    "FILL"),
        ("Frameworks",   "FILL"),
        ("Cloud",        "FILL"),
        ("Databases",    "FILL"),
        ("DevOps",       "FILL"),
    ],

    experience = [
        # FILL: read tools/content.py to see available role functions and bullet keys.
        # Current role: 4-6 bullets. Mid roles: 2-4 bullets. Oldest role: 1-2 bullets.
        # Example: role_company1(["key1", "key2", "key3"]),
    ],

    # cover=None to skip cover letter. Otherwise list of paragraph strings.
    # LinkedIn + work auth paragraphs are auto-appended.
    cover = None,
)
