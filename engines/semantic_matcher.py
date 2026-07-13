"""
==============================================================================
semantic_matcher.py
Advanced Employment & Labor Model (AELM)
==============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Set

@dataclass
class MatchResult:
    resume_skills: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    transferable_skills: List[str] = field(default_factory=list)
    keyword_overlap: float = 0.0
    semantic_score: float = 0.0
    notes: List[str] = field(default_factory=list)

class SemanticMatcher:

    TRANSFERABLE = {
        "Customer Service":["Communication","Problem Solving"],
        "Sales":["Negotiation","Communication"],
        "Project Management":["Leadership","Communication"],
        "Excel":["Data Analysis"],
        "Python":["Automation","Scripting"],
        "SQL":["Data Analysis"]
    }

    def __init__(self,resume,job):
        self.resume=resume
        self.job=job

    def compare(self)->MatchResult:
        result=MatchResult()

        keep=lambda s: s if s.isupper() or any(c.isupper() for c in s[1:]) else s.title()
        r=set(keep(s) for s in self.resume.skills)
        j=set(keep(s) for s in self.job.required_skills)
        job_text=getattr(self.job,"raw_text","").lower()
        resume_text=getattr(self.resume,"raw_text","").lower()

        matched=set(r & j)
        # A resume skill also counts if the job text mentions it,
        # and a job skill counts if the resume text mentions it —
        # this lets section-extracted skills match beyond the fixed list.
        for skill in r:
            if len(skill)>2 and skill.lower() in job_text:
                matched.add(skill)
        for skill in j:
            if len(skill)>2 and skill.lower() in resume_text:
                matched.add(skill)

        result.resume_skills=sorted(r)
        result.required_skills=sorted(j)
        result.matched_skills=sorted(matched)
        result.missing_skills=sorted(j - matched)

        total=max(len(j),1)
        covered=len([s for s in matched if s in j])
        result.keyword_overlap=round(covered/total*100,1)

        transfer=[]
        for skill in r:
            transfer.extend(self.TRANSFERABLE.get(skill,[]))
        result.transferable_skills=sorted(set(transfer))

        score=result.keyword_overlap

        if len(result.missing_skills)==0 and j:
            score+=10
            result.notes.append("All required keywords detected.")
        else:
            result.notes.append(
                f"{len(result.missing_skills)} required skills missing."
            )

        score=min(score,100)
        result.semantic_score=round(score,1)

        if score>=85:
            result.notes.append("Excellent semantic alignment.")
        elif score>=70:
            result.notes.append("Strong alignment.")
        elif score>=50:
            result.notes.append("Moderate alignment.")
        else:
            result.notes.append("Weak alignment. Resume rewrite recommended.")

        return result

def compare_resume_to_job(resume,job):
    return SemanticMatcher(resume,job).compare()
