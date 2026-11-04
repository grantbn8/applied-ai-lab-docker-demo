import React, { useEffect, useState } from 'react';
import { request } from './api';

export default function ProviderPicker({ provider, onChange, busy }) {
  const [status, setStatus] = useState(null);
  const [checking, setChecking] = useState(false);
  async function refresh() {
    setChecking(true);
    try { setStatus(await request('/providers')); }
    catch { setStatus(null); }
    finally { setChecking(false); }
  }
  useEffect(() => { refresh(); }, []);
  return <div className="provider-picker">
    <div className="provider-options" role="group" aria-label="Response provider">
      <button disabled={busy} aria-pressed={provider === 'local'} onClick={() => onChange('local')}>Local · Ollama</button>
      <button disabled={busy} aria-pressed={provider === 'chatgpt'} onClick={() => { onChange('chatgpt'); refresh(); }}>Cloud · ChatGPT</button>
    </div>
    <p>{provider === 'local'
      ? `${status?.local_model || 'Open-weight model'} runs in Docker on this machine. Messages stay local.`
      : 'Runs through Codex with ChatGPT sign-in. Sending shares your message and up to 20 recent messages from this chat with OpenAI. Uses your Codex allowance.'}</p>
    {provider === 'chatgpt' && <div className="auth-status">
      <span>{checking ? 'Checking sign-in…' : status?.chatgpt_authenticated ? 'ChatGPT signed in · No API key' : 'ChatGPT sign-in required'}</span>
      <button type="button" disabled={checking || busy} onClick={refresh}>Refresh status</button>
      {!checking && !status?.chatgpt_authenticated && <code>docker compose exec codex codex login --device-auth</code>}
    </div>}
  </div>;
}
