# Local model

Compose uses the official Ollama image and pulls `gemma3:1b` with the one-shot
`model-init` service. Weights live in the `model-data` named volume, outside Git.

Model reference and license information: https://ollama.com/library/gemma3:1b

Change `MODEL_NAME` in `.env` to another locally runnable Ollama model, then run
`docker compose up -d` to pull it and reconfigure the backend. Do not use cloud model tags.
The server has cloud features disabled. There is no hosted inference fallback.

This demo defaults to CPU inference for portability. Docker Desktop on macOS does
not provide Apple GPU acceleration to this Linux container; small models keep the
demo demonstration manageable. The first download needs internet access;
subsequent inference uses the downloaded weights locally.
