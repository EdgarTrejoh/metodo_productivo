"""Comprobación visual aislada de la captura; ejecutar explícitamente."""
import os
import subprocess
from pathlib import Path

from django.contrib.staticfiles.testing import StaticLiveServerTestCase


class CheckCaptureBrowserQA(StaticLiveServerTestCase):
    def test_capture_and_privacy_in_desktop_and_mobile(self):
        root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env['QA_ORIGIN'] = self.live_server_url
        env['QA_OUTPUT'] = str(root / 'qa_artifacts')
        result = subprocess.run(
            ['node', str(root / 'qa_artifacts' / 'check_capture_qa.cjs')],
            env=env, capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=90,
        )
        self.assertEqual(result.returncode, 0, (result.stdout or '') + (result.stderr or ''))
        print(result.stdout.strip())
