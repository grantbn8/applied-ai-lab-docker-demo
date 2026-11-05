"""Uses a disposable PostgreSQL database; inference is always mocked."""
import unittest
from uuid import uuid4
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.database import connect, initialize
from app.main import app


class DatabaseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Refuse accidental execution against the demo's normal database.
        import os
        if not os.environ.get('PGDATABASE', '').endswith('_test'):
            raise RuntimeError('Integration tests require a database ending in _test')
        with connect() as conn:
            conn.execute('DROP TABLE IF EXISTS messages; DROP TABLE IF EXISTS conversations;')
            conn.execute("CREATE TABLE conversations (id UUID PRIMARY KEY, title TEXT NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT now())")
            conn.execute("CREATE TABLE messages (id BIGSERIAL PRIMARY KEY, conversation_id UUID NOT NULL REFERENCES conversations(id), role TEXT NOT NULL, content TEXT NOT NULL)")
            cls.legacy_id = uuid4()
            conn.execute('INSERT INTO conversations (id,title) VALUES (%s,%s)', (cls.legacy_id, 'Legacy'))
            conn.execute('INSERT INTO messages (conversation_id,role,content) VALUES (%s,%s,%s)', (cls.legacy_id, 'assistant', 'Legacy answer'))
        initialize()
        initialize()  # Migrations must be safe on repeated startup.
        cls.client = TestClient(app)

    def test_legacy_migration(self):
        data = self.client.get('/api/conversations/' + str(self.legacy_id)).json()
        self.assertEqual(data['messages'][0]['provider'], 'local')

    def test_chat_search_providers_and_rollback(self):
        response = self.client.post('/api/conversations')
        self.assertEqual(response.status_code, 201)
        path = '/api/conversations/' + response.json()['id']
        with patch('app.routes.reply', return_value='Local reply'):
            first = self.client.post(path + '/messages', json={'content': 'A title'})
        self.assertEqual(first.status_code, 200)
        with patch('app.routes.reply', return_value='Cloud reply') as reply:
            second = self.client.post(path + '/messages', json={'content': 'UniqueNeedle 100% a_b', 'provider': 'chatgpt'})
            self.assertEqual(reply.call_args.args[1], 'chatgpt')
            self.assertEqual(len(reply.call_args.args[0]), 3)
        saved = second.json()['messages']
        self.assertEqual([m['provider'] for m in saved], ['local', 'local', 'chatgpt', 'chatgpt'])
        for query in ['uniqueneedle', '100%', 'a_b']:
            matches = self.client.get('/api/conversations', params={'q': query}).json()
            self.assertIn(response.json()['id'], [row['id'] for row in matches])
        no_match = self.client.get('/api/conversations', params={'q': 'a%b'}).json()
        self.assertNotIn(response.json()['id'], [row['id'] for row in no_match])
        with patch('app.routes.reply', side_effect=HTTPException(503, 'Provider unavailable')):
            failed = self.client.post(path + '/messages', json={'content': 'Do not save', 'provider': 'chatgpt'})
            self.assertEqual(failed.status_code, 503)
        self.assertEqual(self.client.get(path).json()['messages'], saved)
        self.assertEqual(self.client.post(path + '/messages', json={'content': ' '}).status_code, 422)
        self.assertEqual(self.client.post(path + '/messages', json={'content': 'x', 'provider': 'bad'}).status_code, 422)
        self.assertEqual(self.client.get('/api/conversations/' + str(uuid4())).status_code, 404)


if __name__ == '__main__':
    unittest.main()
