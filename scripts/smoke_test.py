"""Integration check against the running Compose stack; creates one saved chat."""
import json
import urllib.error
import urllib.parse
import urllib.request
from uuid import uuid4

BASE = 'http://localhost:3000/api'


def request(path, body=None, expected=200):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=190) as response:
            assert response.status == expected, response.status
            return json.load(response)
    except urllib.error.HTTPError as error:
        assert error.code == expected, (error.code, error.read().decode())


assert request('/health')['status'] == 'ok'
chat = request('/conversations', {}, expected=201)
path = '/conversations/' + chat['id']
request(path + '/messages', {'content': '   '}, expected=422)
request('/conversations/' + str(uuid4()), expected=404)
marker = 'demo-' + uuid4().hex[:10]
first = request(path + '/messages', {'content': 'Reply with a short greeting.'})
assert len(first['messages']) == 2 and first['messages'][1]['content'].strip()
second = request(path + '/messages', {'content': f'Remember this code: {marker}. Reply OK.'})
assert len(second['messages']) == 4
assert request(path)['messages'] == second['messages']
results = request('/conversations?q=' + marker.upper())
assert chat['id'] in [row['id'] for row in results], 'Search must match message content ignoring case'
assert chat['id'] not in [row['id'] for row in request('/conversations?q=%25')], 'Percent must be literal'
print('PASS: real local inference, follow-up, saved history, search, literal %, validation, and 404')
print('Verification conversation:', chat['id'])
