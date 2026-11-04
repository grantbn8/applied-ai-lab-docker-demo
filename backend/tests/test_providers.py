import unittest
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from app import providers


class ProviderTests(unittest.TestCase):
    messages = [{'role': 'user', 'content': 'hello', 'provider': 'local'}]

    def test_local_never_calls_cloud(self):
        with patch.object(providers, 'local_reply', return_value='local') as local:
            with patch.object(providers.httpx, 'post') as cloud:
                self.assertEqual(providers.reply(self.messages, 'local'), 'local')
                local.assert_called_once_with([{'role': 'user', 'content': 'hello'}])
                cloud.assert_not_called()

    def test_cloud_payload_and_no_fallback(self):
        with patch.object(providers, 'local_reply') as local:
            with patch.object(providers.httpx, 'post', side_effect=httpx.ConnectError('offline')):
                with self.assertRaises(HTTPException) as error:
                    providers.reply(self.messages, 'chatgpt')
                self.assertEqual(error.exception.status_code, 503)
                local.assert_not_called()
            response = httpx.Response(200, json={'content': 'cloud'}, request=httpx.Request('POST', 'http://codex/chat'))
            with patch.object(providers.httpx, 'post', return_value=response) as cloud:
                self.assertEqual(providers.reply(self.messages, 'chatgpt'), 'cloud')
                self.assertEqual(cloud.call_args.kwargs['json'], {'messages': [{'role': 'user', 'content': 'hello'}]})


if __name__ == '__main__':
    unittest.main()
