"""Shared skill and certification vocabulary for the local parsers.

One list, used by both the resume parser and the job parser, so the
two sides of the match always speak the same language. Section-based
extraction in the resume parser supplements this list, so resumes are
not limited to these terms.
"""

COMMON_SKILLS = [
    # programming / data
    "python", "sql", "javascript", "typescript", "java", "c++", "c#", "go",
    "rust", "r", "html", "css", "react", "node", "django", "flask",
    "machine learning", "deep learning", "artificial intelligence", "ai",
    "data analysis", "data science", "data entry", "statistics", "etl",
    "excel", "pivot tables", "vlookup", "power bi", "tableau", "looker",
    # infrastructure / security
    "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "terraform",
    "linux", "windows", "git", "ci/cd", "networking", "cybersecurity",
    "security operations", "soc", "firewall", "active directory",
    "troubleshooting", "help desk", "technical support",
    # operations / logistics / trades
    "logistics", "dispatching", "scheduling", "routing", "fleet",
    "inventory", "warehouse", "forklift", "supply chain", "procurement",
    "quality assurance", "quality control", "manufacturing", "assembly",
    "maintenance", "cdl", "osha",
    # office / business
    "microsoft office", "word", "powerpoint", "outlook", "quickbooks",
    "salesforce", "crm", "erp", "sap", "accounting", "bookkeeping",
    "payroll", "budgeting", "forecasting", "reporting", "documentation",
    "project management", "agile", "scrum",
    # people
    "customer service", "sales", "marketing", "communication",
    "leadership", "teamwork", "training", "coaching", "negotiation",
    "problem solving", "time management", "bilingual", "spanish",
]

COMMON_CERTS = [
    "security+", "network+", "a+", "comptia", "ccna", "ccnp", "cissp",
    "aws certified", "azure certified", "pmp", "capm", "scrum master",
    "six sigma", "cpa", "cpr", "bls", "acls", "servsafe", "osha 10",
    "osha 30", "cdl",
]

ACRONYMS = {"ai": "AI", "aws": "AWS", "gcp": "GCP", "sql": "SQL",
            "etl": "ETL", "soc": "SOC", "crm": "CRM", "erp": "ERP",
            "sap": "SAP", "cdl": "CDL", "osha": "OSHA", "css": "CSS",
            "html": "HTML", "ci/cd": "CI/CD", "r": "R", "bls": "BLS",
            "cpr": "CPR"}


def display(skill: str) -> str:
    """Canonical display form for a skill from the shared vocabulary."""
    return ACRONYMS.get(skill, skill.title())
