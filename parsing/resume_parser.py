"""Section-aware heuristic resume parser (fully local)."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .skills_db import COMMON_SKILLS, COMMON_CERTS, ACRONYMS


@dataclass
class Experience:
    title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: List[str] = field(default_factory=list)


@dataclass
class Education:
    school: Optional[str] = None
    degree: Optional[str] = None
    graduation: Optional[str] = None


@dataclass
class Resume:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    experience: List[Experience] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    raw_text: str = ""


EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}")
YEAR_RANGE = re.compile(r"(19|20)\d{2}\s*[-–—to]+\s*((19|20)\d{2}|present|current)",
                        re.IGNORECASE)
BULLET = re.compile(r"^[\s]*[•·●▪◦*-]\s*")

# Maps header phrases to internal section names. Longer phrases are
# checked first so "core competencies" wins over "core".
SECTION_HEADERS = [
    ("professional summary", "summary"), ("executive summary", "summary"),
    ("career objective", "summary"), ("summary", "summary"),
    ("objective", "summary"), ("profile", "summary"), ("about", "summary"),
    ("core competencies", "skills"), ("technical skills", "skills"),
    ("areas of expertise", "skills"), ("competencies", "skills"),
    ("skills", "skills"),
    ("certifications", "certifications"), ("certificates", "certifications"),
    ("licenses", "certifications"),
    ("professional experience", "experience"),
    ("work experience", "experience"), ("work history", "experience"),
    ("employment history", "experience"), ("employment", "experience"),
    ("experience", "experience"),
    ("research & technical projects", "projects"),
    ("technical projects", "projects"), ("research projects", "projects"),
    ("projects", "projects"),
    ("education & professional development", "education"),
    ("professional development", "education"), ("education", "education"),
    ("academic background", "education"),
    ("achievements", "achievements"), ("accomplishments", "achievements"),
    ("awards", "achievements"), ("honors", "achievements"),
    ("research focus areas", "ignore"), ("references", "ignore"),
    ("volunteer", "ignore"), ("interests", "ignore"), ("hobbies", "ignore"),
]

_SPLIT = re.compile(r"[,;•·●▪◦|\t]|\s{2,}")


def _header_for(line: str):
    """Return (section, inline_content) if line is a section header."""
    stripped = BULLET.sub("", line).strip()
    if len(stripped) > 60:
        return None
    low = stripped.lower()
    for phrase, section in SECTION_HEADERS:
        if low == phrase or low == phrase + ":":
            return section, ""
        if low.startswith(phrase + ":"):
            return section, stripped[len(phrase) + 1:].strip()
        # All-caps header lines like "CORE COMPETENCIES"
        if low.startswith(phrase) and stripped.isupper() \
                and len(low) <= len(phrase) + 12:
            return section, ""
    return None


class ResumeParser:
    def __init__(self, text: str):
        self.text = text
        self.lower = text.lower()
        self.lines = [l.strip() for l in text.splitlines() if l.strip()]
        self.resume = Resume(raw_text=text)
        self.sections: Dict[str, List[str]] = {}

    # ------------------------------------------------------------ pipeline

    def parse(self) -> Resume:
        self._split_sections()
        self._contact()
        self._summary()
        self._skills()
        self._certifications()
        self._experience()
        self._education()
        self._projects()
        self._achievements()
        return self.resume

    # ------------------------------------------------------------ sections

    def _split_sections(self) -> None:
        current = "header"
        for line in self.lines:
            hit = _header_for(line)
            if hit:
                current, inline = hit
                self.sections.setdefault(current, [])
                if inline:
                    self.sections[current].append(inline)
            else:
                self.sections.setdefault(current, []).append(line)

    def _sec(self, name: str) -> List[str]:
        return self.sections.get(name, [])

    # ------------------------------------------------------------ fields

    def _contact(self) -> None:
        if self.lines:
            first = self.lines[0]
            name = first.split(",")[0].strip()
            words = name.split()
            tail_parts = [p.strip() for p in first.split(",")[1:] if p.strip()]
            # "First Last City, State, Country" — peel the city off the name.
            if len(words) >= 3 and len(tail_parts) >= 2:
                name = " ".join(words[:2])
                self.resume.location = " ".join(words[2:]) + ", " + \
                    ", ".join(tail_parts)
            elif len(words) > 3:
                name = " ".join(words[:2])
                rest = first[len(name):].strip(" ,")
                if rest:
                    self.resume.location = rest
            elif tail_parts:
                self.resume.location = ", ".join(tail_parts)
            self.resume.name = name
        m = EMAIL.search(self.text)
        if m:
            self.resume.email = m.group()
        m = PHONE.search(self.text)
        if m:
            self.resume.phone = m.group()
        for line in self.lines:
            ll = line.lower()
            if "linkedin.com" in ll:
                self.resume.linkedin = line
            elif "github.com" in ll:
                self.resume.github = line

    def _is_contact_line(self, line: str) -> bool:
        return bool(EMAIL.search(line) or PHONE.search(line)) or \
            "linkedin.com" in line.lower() or "github.com" in line.lower()

    def _summary(self) -> None:
        body = [l for l in self._sec("summary")
                if not self._is_contact_line(l)]
        if not body:  # fallback: first prose after the contact block
            body = [l for l in self._sec("header")[1:]
                    if not self._is_contact_line(l)][:2]
        if body:
            self.resume.summary = " ".join(body)

    def _skills(self) -> None:
        found: List[str] = []
        for line in self._sec("skills"):
            for part in _SPLIT.split(BULLET.sub("", line)):
                part = part.strip(" .:-")
                if 1 < len(part) <= 40:
                    found.append(part)
        # Supplement with the shared vocabulary found anywhere in the text.
        for s in COMMON_SKILLS:
            if re.search(rf"\b{re.escape(s)}\b", self.lower):
                found.append(ACRONYMS.get(s, s.title()))
        seen, unique = set(), []
        for s in found:
            key = s.lower()
            if key not in seen:
                seen.add(key)
                unique.append(s)
        self.resume.skills = unique

    def _certifications(self) -> None:
        found: List[str] = []
        for line in self._sec("certifications"):
            for part in _SPLIT.split(BULLET.sub("", line)):
                part = part.strip(" .:-")
                if 1 < len(part) <= 60:
                    found.append(part)
        for c in COMMON_CERTS:
            if c in self.lower:
                found.append(c.upper())
        seen, unique = set(), []
        for c in found:
            if c.lower() not in seen:
                seen.add(c.lower())
                unique.append(c)
        self.resume.certifications = unique

    def _experience(self) -> None:
        entry = None
        for line in self._sec("experience"):
            clean = BULLET.sub("", line)
            dates = YEAR_RANGE.search(clean)
            if dates and (entry is None or entry.bullets or entry.title):
                head = clean[:dates.start()].strip(" ,(-—–")
                title, _, company = head.partition(",")
                entry = Experience(
                    title=title.strip() or None,
                    company=company.strip() or None,
                    start_date=dates.group().split("-")[0].strip(),
                    end_date=dates.group().split("-")[-1].strip(),
                )
                tail = clean[dates.end():].strip(" )-—–")
                if tail:
                    entry.bullets.append(tail)
                self.resume.experience.append(entry)
            elif entry is not None:
                entry.bullets.append(clean)
            else:
                entry = Experience(title=clean)
                self.resume.experience.append(entry)

    def _education(self) -> None:
        for line in self._sec("education"):
            clean = BULLET.sub("", line)
            if len(clean) > 80 or clean.lower().startswith("coursework"):
                continue
            school, degree = clean, None
            for sep in ("—", " - ", "–", "|"):
                if sep in clean:
                    school, _, degree = clean.partition(sep)
                    break
            year = re.search(r"(19|20)\d{2}", clean)
            self.resume.education.append(Education(
                school=school.strip() or None,
                degree=(degree or "").strip() or None,
                graduation=year.group() if year else None,
            ))

    def _projects(self) -> None:
        section = [BULLET.sub("", l) for l in self._sec("projects")]
        if section:
            # Keep headline lines; fold description lines into them.
            projects: List[str] = []
            for line in section:
                if len(line) <= 80 and not line.endswith((".", ",")):
                    projects.append(line)
            self.resume.projects = projects or section[:5]
        else:
            self.resume.projects = [
                l for l in self.lines if "project" in l.lower()
            ][:5]

    def _achievements(self) -> None:
        self.resume.achievements = [
            BULLET.sub("", l) for l in self._sec("achievements")
        ]


def parse_resume(text: str) -> Resume:
    return ResumeParser(text).parse()
