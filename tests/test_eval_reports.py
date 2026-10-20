"""Offline evidence-retention checks; no model or network requests."""

import json
import os
import re
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class FreeFallbackAssertions(unittest.TestCase):
    def test_security_contract_accepts_documented_sources_and_gaps(self):
        golden = (SOURCE / ".promptfoo/golden/research-stack.yaml").read_text()
        prompt = (SOURCE / ".promptfoo/prompts/research-stack.txt").read_text()
        block = next(
            part
            for part in golden.split("- description: ")[1:]
            if "--focus security" in part.splitlines()[0]
        )
        assertions = re.findall(r"- type: contains-any\n\s+value: (\[.*\])", block)
        source_line = next(
            line for line in prompt.splitlines() if "security ->" in line
        )
        alternatives = re.findall(r"\[[A-Z]+\]", source_line)
        for evidence in alternatives + [
            "## Coverage gaps\nSecurity sources were unavailable; advisories could not be established."
        ]:
            report = "## Threat and advisory table\n" + evidence
            for values in assertions:
                self.assertTrue(
                    any(tag in report for tag in json.loads(values)), evidence
                )
        # Literal acceptance proves contract compatibility, not rubric accuracy.

    def test_documented_free_fallback_can_pass_literal_assertions(self):
        golden = (SOURCE / ".promptfoo/golden/research-stack.yaml").read_text()
        fixtures = {
            "seo": "## SEO scorecard\nPaid SEO tools were unavailable. Free fallback: web search [WS].",
            "comms": "## Telephony and messaging plan\nPaid comms tools were unavailable. Free fallback: web search [WS].",
        }
        for focus, report in fixtures.items():
            block = next(
                part
                for part in golden.split("- description: ")[1:]
                if "--focus " + focus in part.splitlines()[0]
            )
            assertions = re.findall(r"- type: contains-any\n\s+value: (\[.*\])", block)
            self.assertTrue(assertions)
            for values in assertions:
                self.assertTrue(any(tag in report for tag in json.loads(values)), focus)
            self.assertIn("free fallbacks", block)
            # This tests literal acceptance only; the semantic rubric still needs
            # its configured provider and calibrated evaluation, not this fixture.


class EvaluationReports(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gravity-reports-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "configs").mkdir()
        (self.root / "promptfooconfig.yaml").write_text("fixture")
        (self.root / "configs/another.yaml").write_text("fixture")
        shutil.copy2(SOURCE / ".promptfoo/run-all.sh", self.root / "run-all.sh")
        binary = self.root / "bin"
        binary.mkdir()
        stub = binary / "promptfoo"
        stub.write_text("""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
if os.environ.get("FIXTURE_ERROR"):
    print("fixture CLI diagnostic", file=sys.stderr)
    sys.exit(2)
Path(sys.argv[sys.argv.index("--output")+1]).write_text(json.dumps({
    "results": {"stats": {"successes": 0, "failures": 1, "errors": 0},
                "cases": [{"reason": "fixture assertion failed"}]}}))
print("fixture complete diagnostic")
sys.exit(int(os.environ.get("FIXTURE_EXIT", "0")))
""")
        stub.chmod(0o755)
        self.env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ["PATH"])

    def run_batch(self, error=False):
        env = dict(self.env)
        if error:
            env["FIXTURE_ERROR"] = "1"
        return subprocess.run(
            ["bash", str(self.root / "run-all.sh")],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def latest(self):
        pointer = self.root / "reports/latest-run"
        self.assertTrue(pointer.is_symlink(), "latest batch pointer missing")
        target = pointer.resolve(strict=True)
        self.assertEqual(target.parent, self.root / "reports")
        return target

    def test_failed_cases_and_diagnostics_survive_exit_privately(self):
        result = self.run_batch()
        self.assertNotEqual(result.returncode, 0)
        batch = self.latest()
        self.assertIn(str(batch), result.stdout)
        self.assertEqual(stat.S_IMODE(batch.stat().st_mode), 0o700)
        for skill in ("planning-stack", "another"):
            report = batch / (skill + ".json")
            self.assertEqual(
                json.loads(report.read_text())["results"]["cases"][0]["reason"],
                "fixture assertion failed",
            )
            self.assertEqual(stat.S_IMODE(report.stat().st_mode), 0o600)
            log = batch / (skill + ".log")
            self.assertIn("fixture complete diagnostic", log.read_text())
            self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o600)

    def test_error_batch_retains_logs_without_reusing_stale_results(self):
        self.run_batch()
        previous = self.latest()
        previous_report = (previous / "planning-stack.json").read_bytes()
        result = self.run_batch(error=True)
        self.assertNotEqual(result.returncode, 0)
        latest = self.latest()
        self.assertNotEqual(latest, previous)
        self.assertIn("invalid, missing or empty evaluation result", result.stdout)
        self.assertFalse((latest / "planning-stack.json").exists())
        self.assertIn(
            "fixture CLI diagnostic", (latest / "planning-stack.log").read_text()
        )
        self.assertEqual(
            (previous / "planning-stack.json").read_bytes(), previous_report
        )

    def test_valid_failed_cases_are_not_runner_errors(self):
        self.env["FIXTURE_EXIT"] = "100"
        result = self.run_batch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("2 failed, 0 errors", result.stdout)
        self.assertIn("0 runner errors", result.stdout)
        self.assertTrue((self.latest() / "planning-stack.json").is_file())


class Review53Contracts(unittest.TestCase):
    def assertions(self, focus):
        golden=(SOURCE/'.promptfoo/golden/research-stack.yaml').read_text()
        block=next(p for p in golden.split('- description: ')[1:] if '--focus '+focus in p.splitlines()[0])
        return [json.loads(v) for v in re.findall(r'- type: contains-any\n\s+value: (\[.*\])',block)]
    def accepts(self,focus,report):
        return all(any(tag in report for tag in values) for values in self.assertions(focus))
    def test_generic_heading_and_web_tags_cannot_prove_focus_sources(self):
        for focus,heading in [('security','Threat and advisory table'),('seo','SEO scorecard'),('comms','Telephony and messaging plan')]:
            for noise in ['## Coverage gaps','Web search [WS].','## Coverage Gaps\nWeb search [WS].']:
                with self.subTest(focus=focus,noise=noise):self.assertFalse(self.accepts(focus,'## '+heading+'\n'+noise))
    def test_documented_sources_and_specific_fallback_controls_remain_accepted(self):
        for focus,heading,tag,gap in [('security','Threat and advisory table','[OSV]','Security sources were unavailable; advisories could not be established.'),('seo','SEO scorecard','[DFS]','Paid SEO tools were unavailable. Free fallback: web search [WS].'),('comms','Telephony and messaging plan','[FCC]','Paid comms tools were unavailable. Free fallback: web search [WS].')]:
            for evidence in [tag,gap]:
                with self.subTest(focus=focus,evidence=evidence):self.assertTrue(self.accepts(focus,'## '+heading+'\n'+evidence+'\n## Coverage gaps'))
    def test_project_json_credential_values_are_environment_references(self):
        docs=(SOURCE/'docs/mcp-servers.md').read_text()
        count=0
        for block in re.findall(r'```json\n(.*?)\n```',docs,re.S):
            for server in json.loads(block).get('mcpServers',{}).values():
                for key,value in server.get('env',{}).items():
                    if key.endswith(('_API_KEY','_PASSWORD','_USERNAME')):
                        count+=1
                        with self.subTest(key=key):self.assertEqual(value,'${'+key+'}')
        self.assertGreaterEqual(count,4)
    def site_servers(self):
        program='import {mcpServers,researchServers} from '+json.dumps((SOURCE/'site/src/lib/data/mcp-servers.ts').as_uri())+';console.log(JSON.stringify([...mcpServers,...researchServers]));'
        result=subprocess.run(['node','--experimental-strip-types','--input-type=module','-e',program],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads(result.stdout)
    def test_site_credentials_use_environment_references(self):
        found=[]
        for server in self.site_servers():
            for key,value in server['config'].get('env',{}).items():
                if key.endswith(('_API_KEY','_PASSWORD','_USERNAME')):
                    found.append(key)
                    with self.subTest(key=key):self.assertEqual(value,'${'+key+'}')
        self.assertIn('DATAFORSEO_PASSWORD',found)
    def test_site_npm_launches_are_noninteractive(self):
        for server in self.site_servers():
            if server['type']=='npm':
                with self.subTest(server=server['slug']):
                    self.assertEqual(server['config']['command'],'npx')
                    self.assertEqual(server['config']['args'][0],'-y')
    def test_nonzero_cli_with_positive_results_never_prints_pass_for_that_skill(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'configs').mkdir();(root/'promptfooconfig.yaml').write_text('owned fixture');(root/'configs/another.yaml').write_text('owned fixture')
            shutil.copy2(SOURCE/'.promptfoo/run-all.sh',root/'run-all.sh');(root/'bin').mkdir();stub=root/'bin/promptfoo'
            stub.write_text('#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\nPath(sys.argv[sys.argv.index("--output")+1]).write_text(json.dumps({"results":{"stats":{"successes":2,"failures":0,"errors":0}}}))\nsys.exit(2)\n');stub.chmod(0o755)
            result=subprocess.run(['bash',str(root/'run-all.sh')],env={**os.environ,'PATH':str(root/'bin')+os.pathsep+os.environ['PATH']},capture_output=True,text=True,timeout=15)
            self.assertNotEqual(result.returncode,0);self.assertIn('2 runner errors',result.stdout)
            self.assertNotIn('  ✓ 2 passed',result.stdout)
            self.assertEqual(len(list((root/'reports/latest-run').resolve().glob('*.json'))),2)
    def test_ci_shards_cover_every_discovered_case_once(self):
        helper=SOURCE/'tests/run_ci_tests.py';self.assertTrue(helper.is_file())
        lists=[]
        for shard in ['hooks','other']:
            result=subprocess.run(['python3',str(helper),'--shard',shard,'--list-only'],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr);lists.append(json.loads(result.stdout))
        import sys
        sys.path.insert(0,str(SOURCE/'tests'))
        def flatten(s):
            for c in s:
                if isinstance(c,unittest.TestSuite):yield from flatten(c)
                else:yield c.id()
        expected=sorted(flatten(unittest.defaultTestLoader.discover(str(SOURCE/'tests'),pattern='test_*.py')))
        self.assertTrue(all(lists));self.assertFalse(set(lists[0])&set(lists[1]));self.assertEqual(sorted(lists[0]+lists[1]),expected)


if __name__ == "__main__":
    unittest.main()
