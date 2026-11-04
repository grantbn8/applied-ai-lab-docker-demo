FROM node:22-bookworm-slim AS cli
RUN npm install -g @openai/codex@0.166.0

FROM python:3.12-slim
COPY --from=cli /usr/local/bin/node /usr/local/bin/node
COPY --from=cli /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/@openai/codex/bin/codex.js /usr/local/bin/codex \
    && useradd --create-home --uid 10001 runner \
    && mkdir -p /home/runner/.codex /workspace \
    && chown -R runner:runner /home/runner /workspace
WORKDIR /service
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
ENV CODEX_HOME=/home/runner/.codex
USER runner
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
