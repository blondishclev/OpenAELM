"""
==============================================================================
resume_rewriter.py
Advanced Employment & Labor Model (AELM)
==============================================================================
"""

from dataclasses import dataclass
from typing import List

@dataclass
class RewriteResult:
    resume_text: str
    mode: str
    notes: List[str]

class ResumeRewriter:

    MODES = {
        "ats": "ATS Optimized",
        "minimal": "Minimal Edit",
        "executive": "Executive",
        "entry": "Entry Level",
        "plain": "Plain Text"
    }

    def __init__(self, resume, job=None):
        self.resume = resume
        self.job = job

    def rewrite(self, mode="ats"):
        notes = [
            "Only information found in the original resume was used.",
            "No experience, metrics, or credentials were invented."
        ]

        lines = []

        if self.resume.name:
            lines.append(self.resume.name)
        contact = " | ".join(filter(None, [
            self.resume.email,
            self.resume.phone,
            self.resume.linkedin,
            self.resume.github
        ]))
        if contact:
            lines.append(contact)

        if self.resume.summary:
            summary = self.resume.summary
            for h in ("professional summary", "summary", "objective"):
                if summary.lower().startswith(h):
                    summary = summary[len(h):].lstrip(" :").strip()
            if summary:
                lines.extend(["", "PROFESSIONAL SUMMARY", summary])

        if self.resume.skills:
            skills = sorted(set(self.resume.skills))
            if self.job:
                wanted = [s for s in skills if s in self.job.required_skills]
                other = [s for s in skills if s not in wanted]
                skills = wanted + other
            lines.extend(["", "SKILLS", ", ".join(skills)])

        if self.resume.certifications:
            lines.extend([
                "",
                "CERTIFICATIONS",
                *self.resume.certifications
            ])

        if self.resume.experience:
            lines.extend(["", "EXPERIENCE"])
            for e in self.resume.experience:
                head = " — ".join(filter(None, [e.title, e.company]))
                dates = "–".join(filter(None, [e.start_date, e.end_date]))
                if dates:
                    head = f"{head} ({dates})" if head else dates
                if head:
                    lines.append(head)
                lines.extend(f"• {b}" for b in e.bullets)

        if self.resume.education:
            lines.extend(["", "EDUCATION"])
            for ed in self.resume.education:
                entry = " — ".join(filter(None, [ed.school, ed.degree]))
                if entry:
                    lines.append(entry)

        if self.resume.projects:
            lines.extend(["", "PROJECTS"])
            lines.extend(f"• {p}" for p in self.resume.projects)

        if self.resume.achievements:
            lines.extend(["", "ACHIEVEMENTS"])
            lines.extend(f"• {a}" for a in self.resume.achievements)

        text = "\n".join(lines)

        if mode == "plain":
            text = text.replace("• ", "- ")

        return RewriteResult(
            resume_text=text,
            mode=self.MODES.get(mode, "ATS Optimized"),
            notes=notes
        )

def rewrite_resume(resume, job=None, mode="ats"):
    return ResumeRewriter(resume, job).rewrite(mode)
