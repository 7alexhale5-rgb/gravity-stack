#!/usr/bin/env python3
"""Run: python3 -m unittest discover -s tests -p test_installer.py

Exercises the real master installer. Only prerequisite phases and external git
are stubbed; HOME/PATH are subprocess-local. No network or host installation.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class PhaseSix(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='gravity-phase6-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.toolkit = self.root / 'toolkit'
        (self.toolkit / 'scripts').mkdir(parents=True)
        shutil.copy2(SOURCE / 'toolkit/install.sh', self.toolkit / 'install.sh')
        for name in ['01-foundation.sh', '02-claude-code.sh', '03-mcp-servers.sh', '04-hooks.sh', '05-verify.sh']:
            (self.toolkit / 'scripts' / name).write_text('#!/usr/bin/env bash\nexit 0\n')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.script('uname', '#!/bin/sh\nif [ "${1:-}" = -m ]; then echo arm64; else echo Darwin; fi\n')
        self.script('git', '''#!/usr/bin/env bash
set -eu
printf 'clone\\n' >> "$HOME/calls"
dest="${@: -1}"
mkdir -p "$dest"
cat > "$dest/install.sh" <<'INSTALL'
#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" >> "$HOME/installed-args"
INSTALL
chmod +x "$dest/install.sh"
''')
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin)+os.pathsep+os.environ['PATH'])

    def script(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def run_installer(self, *args):
        return subprocess.run(['bash', str(self.toolkit / 'install.sh'), *args], env=self.env,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=15)

    def no_install(self, *args):
        before = sorted(str(p.relative_to(self.home)) for p in self.home.rglob('*'))
        result = self.run_installer(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, sorted(str(p.relative_to(self.home)) for p in self.home.rglob('*')))
        return result.stdout

    def test_closed_stdin_skips(self):
        self.assertIn('No terminal to ask on. Skipping', self.no_install())

    def test_explicit_skip(self):
        self.assertIn('Skipped (--skip-dev-protocol)', self.no_install('--skip-dev-protocol'))

    def test_skip_overrides_yes(self):
        self.assertIn('Skipped (--skip-dev-protocol)', self.no_install('--yes', '--skip-dev-protocol'))

    def test_dry_run(self):
        self.assertIn('would ask:', self.no_install('--dry-run'))

    def test_dry_yes_claude(self):
        self.assertIn('--target claude --yes', self.no_install('--dry-run', '--yes'))

    def test_dry_yes_both(self):
        (self.home / '.agents').mkdir()
        self.assertIn('--target both --yes', self.no_install('--dry-run', '--yes'))

    def test_dry_skip(self):
        self.assertIn('Skipped (--skip-dev-protocol)', self.no_install('--dry-run', '--skip-dev-protocol'))

    def test_yes_default_claude(self):
        result = self.run_installer('--yes')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / 'installed-args').read_text(), '--target claude --yes\n')
        self.assertEqual((self.home / 'calls').read_text(), 'clone\n')

    def test_yes_existing_agents_both(self):
        (self.home / '.agents').mkdir()
        result = self.run_installer('--yes')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / 'installed-args').read_text(), '--target both --yes\n')
        self.assertEqual((self.home / 'calls').read_text(), 'clone\n')


if __name__ == '__main__':
    unittest.main(verbosity=2)
