"""Exercise real hooks in disposable repositories, using nonfunctional fixtures."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

SOURCE = Path(__file__).resolve().parents[1]


def run(repo, *args, ok=True, env=None):
    result = subprocess.run(args, cwd=repo, env=env, capture_output=True, text=True)
    if ok and result.returncode:
        raise AssertionError(result.stderr)
    if not ok and result.returncode == 0:
        raise AssertionError('Expected operation to be blocked')
    return result


with tempfile.TemporaryDirectory(prefix='demo-hook-test-') as directory:
    repo = Path(directory) / 'work'
    repo.mkdir()
    remote = Path(directory) / 'remote.git'
    run(repo, 'git', 'init', '-b', 'main')
    run(repo, 'git', 'config', 'user.name', 'Hook test')
    run(repo, 'git', 'config', 'user.email', 'hook-test@example.invalid')
    run(repo, 'git', 'init', '--bare', str(remote))
    run(repo, 'git', 'remote', 'add', 'origin', str(remote))
    # Seed an intentionally bad historical fixture BEFORE installing any hooks.
    # This is not a real credential; no fixture is ever uploaded to GitHub.
    (repo / 'fixture.txt').write_text('token = "' + 'gh' + 'p_' + 'Ab3dE7fGh9JkLm2NpQr5StUv8WxYz0123456' + '"\n')
    run(repo, 'git', 'add', 'fixture.txt')
    run(repo, 'git', 'commit', '-m', 'Synthetic historical fixture')
    run(repo, 'git', 'tag', 'test-tag')
    shutil.copytree(SOURCE / '.githooks', repo / '.githooks')
    (repo / 'scripts').mkdir()
    shutil.copy(SOURCE / 'scripts/security-check.sh', repo / 'scripts/security-check.sh')
    shutil.copy(SOURCE / '.gitleaks.toml', repo / '.gitleaks.toml')
    run(repo, 'git', 'config', 'core.hooksPath', '.githooks')
    (repo / 'staged.txt').write_text((repo / 'fixture.txt').read_text())
    run(repo, 'git', 'add', 'staged.txt')
    run(repo, 'git', 'commit', '-m', 'Must be blocked', ok=False)
    run(repo, 'git', 'push', 'origin', 'main', ok=False)
    run(repo, 'git', 'push', 'origin', 'test-tag', ok=False)
    refs = run(repo, 'git', '--git-dir', str(remote), 'show-ref', ok=False)
    assert not refs.stdout, 'Blocked pushes must not create remote refs'
    run(repo, 'git', 'reset', '--', 'staged.txt')
    (repo / 'auth.json').write_text('{}')
    run(repo, 'git', 'add', 'auth.json')
    denied = run(repo, 'git', 'commit', '-m', 'Forbidden path', ok=False)
    assert 'Blocked credential/data path' in denied.stderr
    run(repo, 'git', 'reset', '--', 'auth.json')
    (repo / 'clean.txt').write_text('Clean demo content\n')
    run(repo, 'git', 'add', 'clean.txt')
    fake_bin = Path(directory) / 'bin'
    fake_bin.mkdir()
    docker = fake_bin / 'docker'
    docker.write_text('#!/bin/sh\necho scanner-unavailable >&2\nexit 42\n')
    docker.chmod(0o755)
    env = {**os.environ, 'PATH': str(fake_bin) + os.pathsep + os.environ['PATH']}
    failed = run(repo, 'git', 'commit', '-m', 'Scanner must run', ok=False, env=env)
    assert 'scanner-unavailable' in failed.stderr
print('PASS: staged secret, initial push, tag push, credential filename, and scanner failure all blocked')
