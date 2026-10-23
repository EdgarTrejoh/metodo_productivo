"""Recorrido visual aislado de C-01; ejecutar explícitamente."""
import os
import subprocess
from pathlib import Path

from django.contrib.staticfiles.testing import StaticLiveServerTestCase


class CheckTwoTabsBrowserQA(StaticLiveServerTestCase):
    def test_old_tab_does_not_change_new_execution(self):
        root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env['QA_ORIGIN'] = self.live_server_url
        env['QA_OUTPUT'] = str(root / 'qa_artifacts')
        result = subprocess.run(
            ['node', str(root / 'qa_artifacts' / 'c01_two_tabs.cjs')],
            env=env, capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=90,
        )
        self.assertEqual(result.returncode, 0, (result.stdout or '') + (result.stderr or ''))
        print(result.stdout.strip())
