import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException
import main


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'CODEX_HOME': self.home.name})
        self.env.start()
        self.body = main.ChatInput(messages=[{'role': 'user', 'content': 'hello'}])

    def tearDown(self):
        self.env.stop()
        self.home.cleanup()

    def test_no_login_and_api_key_rejected(self):
        for auth in [{}, {'auth_mode': 'apikey', 'OPENAI_API_KEY': 'test'}]:
            Path(self.home.name, 'auth.json').write_text(json.dumps(auth))
            with patch('main.subprocess.run') as run:
                with self.assertRaises(HTTPException) as error:
                    main.chat(self.body)
                self.assertEqual(error.exception.status_code, 503)
                run.assert_not_called()

    def test_cloud_command_and_output(self):
        Path(self.home.name, 'auth.json').write_text(json.dumps({'auth_mode': 'chatgpt', 'tokens': {'test': True}}))
        def execute(command, **kwargs):
            self.assertIn('forced_login_method="chatgpt"', command)
            self.assertIn('features.shell_tool=false', command)
            self.assertIn('--ephemeral', command)
            self.assertNotIn('OPENAI_API_KEY', kwargs['env'])
            self.assertNotIn('CODEX_API_KEY', kwargs['env'])
            self.assertIn('hello', kwargs['input'])
            Path(command[command.index('--output-last-message') + 1]).write_text('**Hello**')
            return type('Result', (), {'returncode': 0})()
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'never-forward', 'CODEX_API_KEY': 'never-forward'}):
            with patch('main.subprocess.run', side_effect=execute):
                self.assertEqual(main.chat(self.body), {'content': '**Hello**'})

    def test_timeout_releases_lock(self):
        Path(self.home.name, 'auth.json').write_text(json.dumps({'auth_mode': 'chatgpt', 'tokens': {'test': True}}))
        with patch('main.subprocess.run', side_effect=main.subprocess.TimeoutExpired('codex', 170)):
            with self.assertRaises(HTTPException) as error:
                main.chat(self.body)
            self.assertEqual(error.exception.status_code, 504)
        self.assertFalse(main.run_lock.locked())


if __name__ == '__main__':
    unittest.main()
