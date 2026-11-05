# Repository guidance

## Purpose
This is a small teaching repository for Docker Compose and AI-assisted development.
Keep the code easy to read, explain, and modify.

## Architecture
- Use React, FastAPI, PostgreSQL, and a separate Ollama model service.
- The frontend calls the backend. Database and model access belong in the backend.
- Default to local Ollama; allow explicit ChatGPT selection through headless Codex.
- Use ChatGPT account authentication, never API keys or automatic provider fallbacks.
- Clearly label cloud requests and persist the provider on each message.
- Manage application services through Docker Compose.

## Code organization
- Keep modules focused on one responsibility.
- Separate API routes, database access, and model integration.
- Prefer simple functions and small components.
- Add abstractions and dependencies only when they solve a concrete need.

## Configuration
- Read configuration from environment variables; document them in .env.example.
- Never commit secrets, downloaded model weights, or database files.

## Documentation
- Update README.md when setup steps or behavior change.
- Update its Mermaid diagram whenever services, connections, or persistence change.

## Verification
- Run checks appropriate to the change, including Compose validation for container changes.
- Check chat, history persistence, search, and model failure handling when changing those paths.
- Report what was checked and anything that could not be verified.


## Security: mandatory before any commit, push, or release
- Never commit/upload real passwords, API keys, OAuth tokens, private keys, .env
  contents, Codex auth files, or credential/data volume exports.
- Install hooks with `bash scripts/install-hooks.sh`. Run
  `bash scripts/security-check.sh staged` before committing and
  `bash scripts/security-check.sh history` before pushing or releasing.
- Stop on findings OR scanner errors. Never bypass hooks, disable scanners,
  use blanket exclusions, or publish first and clean up later.
- Report only filenames and redacted descriptions. Never print discovered secrets.
- If a real credential was exposed, stop publication and require revocation/rotation;
  removing it from the newest file does not remove it from Git history.
- The literal `classroom-demo` database password is a non-secret local teaching
  default. Tests use nonfunctional placeholders. Neither tests nor example files
  are excluded from secret scanning.
- CI must never receive ChatGPT authentication or OpenAI API keys. Use mocks.

## Git workflow
- Only the owner writes upstream. Students fork and push to their own repositories.
- Normal development goes to dev; main changes require a PR and passing ci-success.
- Never force-push or delete main/dev, or bypass protection to resolve a failed check.
- Promote dev to main with a merge commit; then fast-forward dev to main.


## Classroom distribution and notifications
- This upstream is for cloning/forking, not student submissions. Students push
  and run Actions only in their own repositories.
- Keep CI limited to main/dev pushes, authorized manual runs, and reusable calls.
  Do not add pull_request, pull_request_target, issue, comment, fork, or scheduled
  triggers without an explicit owner request.
- Keep Issues, Discussions, and wiki disabled upstream. Do not add auto-comment,
  mention, review-request, or student notification bots.
- Do not create deliberate failing upstream CI runs for routine verification.
  Test failure handling locally; historical gate probes already proved enforcement.

## Vulnerability remediation
- Follow [VULNERABILITY_REMEDIATION.md](VULNERABILITY_REMEDIATION.md) for dependency findings.
- Keep vulnerability audits required by ci-success; never suppress findings or scanner failures to merge.
- Cleanup documentation and commands must target this Compose project only; never document or run Docker-wide deletion for this project.
