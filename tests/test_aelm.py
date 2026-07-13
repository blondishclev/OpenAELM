"""AELM test suite.

Run from the directory ABOVE the package folder:
    python -m pytest <package>/tests -v
or with the standard library only:
    python -m unittest discover <package>/tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

PKG_PARENT = Path(__file__).resolve().parents[2]
PKG_NAME = Path(__file__).resolve().parents[1].name
sys.path.insert(0, str(PKG_PARENT))

import importlib

pkg = importlib.import_module(PKG_NAME)
for _sub in ("parsing", "engines", "pipeline", "session", "export", "ui"):
    importlib.import_module(f"{PKG_NAME}.{_sub}")

parse_resume = pkg.parsing.parse_resume
parse_job = pkg.parsing.parse_job
load_file = pkg.parsing.load_file
compare = pkg.engines.compare_resume_to_job
evaluate_ats = pkg.engines.evaluate_ats
evaluate_fraud = pkg.engines.evaluate_fraud
rewrite_resume = pkg.engines.rewrite_resume

RESUME = """Jane Doe
jane.doe@email.com | 555-123-4567
Summary: Data analyst with 4 years of experience in SQL, Python, and Excel.
Skills: Python, SQL, Excel, AWS, communication
Education: BS Statistics, University of Georgia
"""

JOB = """Data Analyst - Remote
We seek a data analyst with SQL, Python, Excel skills. AWS a plus.
Salary: $70,000 - $85,000. Full-time. Bachelor's degree required.
3+ years experience. Strong communication and leadership.
"""

SCAM_JOB = """Easy remote job! To start, pay for training via gift card.
Message us on Telegram. We also accept bitcoin. Send your bank account
details today for a check deposit.
"""


class TestParsing(unittest.TestCase):
    def test_load_txt_file(self):
        with tempfile.NamedTemporaryFile(
                "w", suffix=".txt", delete=False) as f:
            f.write(RESUME)
        self.assertEqual(load_file(f.name), RESUME)

    def test_load_missing_file_raises(self):
        with self.assertRaises(Exception):
            load_file("no_such_file_xyz.txt")

    def test_resume_contact(self):
        r = parse_resume(RESUME)
        self.assertEqual(r.email, "jane.doe@email.com")
        self.assertIn("555-123-4567", r.phone or "")
        self.assertEqual(r.name, "Jane Doe")

    def test_resume_skills(self):
        skills = [s.lower() for s in parse_resume(RESUME).skills]
        for expected in ("python", "sql", "excel"):
            self.assertIn(expected, skills)

    def test_job_fields(self):
        j = parse_job(JOB)
        self.assertTrue(j.salary and "70,000" in j.salary)
        req = [s.lower() for s in j.required_skills + j.preferred_skills]
        self.assertIn("python", req)
        self.assertIn("sql", req)


class TestEngines(unittest.TestCase):
    def setUp(self):
        self.resume = parse_resume(RESUME)
        self.job = parse_job(JOB)
        self.match = compare(self.resume, self.job)

    def test_match_score_bounds(self):
        self.assertGreaterEqual(self.match.semantic_score, 0)
        self.assertLessEqual(self.match.semantic_score, 100)

    def test_matching_resume_scores_high(self):
        self.assertGreaterEqual(self.match.semantic_score, 50)
        matched = [s.lower() for s in self.match.matched_skills]
        self.assertIn("python", matched)
        self.assertIn("sql", matched)

    def test_ats_score_bounds(self):
        a = evaluate_ats(self.resume, self.job, self.match)
        self.assertGreaterEqual(a.survivability_score, 0)
        self.assertLessEqual(a.survivability_score, 100)
        self.assertTrue(a.verdict)

    def test_fraud_clean_job_low_risk(self):
        f = evaluate_fraud(JOB)
        self.assertEqual(f.verdict, "Low Risk")
        self.assertEqual(f.flags, [])

    def test_fraud_scam_job_flagged(self):
        f = evaluate_fraud(SCAM_JOB)
        self.assertGreaterEqual(f.risk_score, 70)
        self.assertIn("Likely Scam", f.verdict)
        self.assertTrue(f.warning)

    def test_rewrite_is_truthful(self):
        result = rewrite_resume(self.resume, self.job)
        self.assertIn("jane.doe@email.com", result.resume_text)
        # Nothing invented: every year mentioned must come from the input.
        for token in ("2019", "2030", "PhD", "Master"):
            self.assertNotIn(token, result.resume_text)


class TestPipelineAndExport(unittest.TestCase):
    def test_full_pipeline_and_export(self):
        session = pkg.session.session
        session.clear_all()
        session.resume_text, session.job_text = RESUME, JOB
        dashboard = pkg.pipeline.analyze(progress=lambda _msg: None)
        self.assertTrue(session.analyzed)
        self.assertTrue(dashboard.recommended_next_action)

        with tempfile.TemporaryDirectory() as tmp:
            engine = pkg.export.ExportEngine(output_dir=tmp)
            for fmt in ("txt", "md", "json"):
                path = Path(engine.export(fmt, dashboard))
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 0)
            with open(path) as f:  # last one is json
                self.assertIn("ats", json.dumps(json.load(f)).lower())
        session.clear_all()


class TestUIFallback(unittest.TestCase):
    def test_ui_functions_do_not_crash(self):
        ui = pkg.ui
        ui.banner("AELM", "test")
        ui.info("info")
        ui.success("ok")
        ui.error("bad")
        ui.hint("hint")
        ui.rule("TITLE")
        ui.kv_table([("Score", "80/100"), ("Risk", "High")])
        ui.bullets("Items", ["a", "b"])
        ui.bullets("Empty", [], empty="(none)")
        ui.panel("body", title="t")


RESEARCH_RESUME = """Rahshawn Francis Atlanta, Georgia, United States
Email: user@example.com
PROFESSIONAL SUMMARY
Independent AI systems researcher focused on behavioral simulation
frameworks, multi-agent systems, and adaptive optimization.
CORE COMPETENCIES
AI Systems Architecture, Multi-Agent Systems, Behavioral Analytics,
Cybersecurity Fundamentals, Computational Modeling
RESEARCH & TECHNICAL PROJECTS
AELM Framework v2 (Adaptive Employment Lifecycle Modeling)
Designed an AI-assisted employment intelligence framework.
EDUCATION & PROFESSIONAL DEVELOPMENT
Destiny Academy — High School Diploma
Coursework: CompTIA Security+ Coursework, AI & Machine Learning Foundations
"""


class TestRealWorldRegressions(unittest.TestCase):
    """Cases derived from failures observed with a real resume/job pair."""

    def setUp(self):
        self.r = parse_resume(RESEARCH_RESUME)

    def test_name_excludes_city(self):
        self.assertEqual(self.r.name, "Rahshawn Francis")
        self.assertIn("Atlanta", self.r.location or "")

    def test_summary_excludes_header(self):
        self.assertNotIn("PROFESSIONAL SUMMARY", self.r.summary or "")
        self.assertTrue(self.r.summary.startswith("Independent"))

    def test_core_competencies_extracted(self):
        self.assertIn("Multi-Agent Systems", self.r.skills)
        self.assertGreaterEqual(len(self.r.skills), 5)

    def test_education_section_parsed(self):
        schools = [e.school for e in self.r.education]
        self.assertIn("Destiny Academy", schools)

    def test_rewrite_header_not_duplicated(self):
        result = rewrite_resume(self.r)
        self.assertEqual(
            result.resume_text.count("PROFESSIONAL SUMMARY"), 1)

    def test_mismatched_job_scores_low(self):
        job = parse_job(
            "Logistics Planner. Excel, Pivot Tables, dispatching, "
            "scheduling and fleet data required. 1 year dispatching.")
        m = compare(self.r, job)
        self.assertLess(m.semantic_score, 30)
        self.assertIn("Excel", m.missing_skills)

    def test_matched_job_scores_high(self):
        job = parse_job(
            "AI Researcher. Machine learning, multi-agent systems, "
            "behavioral modeling, cybersecurity experience required.")
        m = compare(self.r, job)
        self.assertGreaterEqual(m.semantic_score, 70)
        self.assertIn("Multi-Agent Systems", m.matched_skills)


if __name__ == "__main__":
    unittest.main(verbosity=2)
