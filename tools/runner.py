"""
Single-call generator for job applications.

Usage in a job script:
    from tools.runner import generate

    generate(
        company    = "CompanyName",
        role       = "Role Title",
        date       = "March 17, 2026",
        dept       = "Team or Department",
        accent     = (68, 114, 196),
        summary    = "...",
        skills     = [("Languages", "Java, Python"), ...],
        experience = [...],   # use role_* helpers from tools.content
        cover      = ["Para 1", "Para 2", "Para 3"],
    )

Creates output/[company] - [role] - [date]/ automatically.
Appends LinkedIn and work-auth paragraphs to the cover letter automatically.
"""

import os
from datetime import datetime
from tools.docx_builder import ResumeBuilder, CoverLetterBuilder, WORK_AUTH_PARA, LINKEDIN_PARA, USER_NAME


def generate(company, role, date, dept, accent, summary, skills, experience, cover=None):
    """Build resume + cover letter and save to output/[company] - [role] - [date]/."""
    root        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder_date = datetime.strptime(date, "%B %d, %Y").strftime("%Y-%m-%d")
    out         = os.path.join(root, "output", "applied", f"{company} - {role} - {folder_date}")
    os.makedirs(out, exist_ok=True)

    # Resume
    r = ResumeBuilder(accent=accent)
    r.header()
    r.summary(summary)
    r.skills(skills)
    r.experience(experience)
    r.education()
    name_slug = "".join(c for c in USER_NAME if c.isalpha())
    r.save(os.path.join(out, f"{name_slug}_{company}.docx"))

    # Cover letter — LinkedIn + work-auth always appended; pass cover=None to skip
    if cover is not None:
        cl = CoverLetterBuilder(accent=accent)
        cl.header()
        cl.salutation(date=date, to="Hiring Team", company=company, city=dept, role=role)
        cl.body(cover + [LINKEDIN_PARA, WORK_AUTH_PARA])
        cl.sign_off()
        cl.save(os.path.join(out, f"message_{company}.docx"))
