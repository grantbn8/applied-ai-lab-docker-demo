import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { request } from './api';
import Message from './Message';
import ProviderPicker from './ProviderPicker';
import './styles.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [active, setActive] = useState(null);
  const [query, setQuery] = useState('');
  const [provider, setProvider] = useState('local');
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState(null);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const bottom = useRef(null);

  useEffect(() => {
    let current = true;
    const timer = setTimeout(() => {
      request(`/conversations?q=${encodeURIComponent(query)}`)
        .then(data => { if (current) setConversations(data); })
        .catch(err => { if (current) setError(err.message); });
    }, 150);
    return () => { current = false; clearTimeout(timer); };
  }, [query, revision]);

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }); }, [active, busy, pending]);

  async function openConversation(id) {
    setBusy(true); setError('');
    try { setActive(await request(`/conversations/${id}`)); setDraft(''); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function send(event) {
    event.preventDefault();
    if (!draft.trim() || busy) return;
    const content = draft.trim();
    setBusy(true); setError(''); setPending(content); setDraft('');
    try {
      let conversation = active;
      if (!conversation) {
        conversation = await request('/conversations', { method: 'POST' });
        setActive({ ...conversation, messages: [] });
      }
      const updated = await request(`/conversations/${conversation.id}/messages`, {
        method: 'POST', body: JSON.stringify({ content, provider }),
      });
      setActive(updated); setDraft(''); setQuery('');
    } catch (err) { setError(err.message); setDraft(content); }
    finally { setBusy(false); setPending(null); setRevision(value => value + 1); }
  }

  return <div className="app">
    <aside>
      <div className="brand">Local Chat Lab<span>APPLIED AI · DOCKER DEMO</span></div>
      <button className="new-chat" disabled={busy} onClick={() => { setActive(null); setDraft(''); setError(''); }}>+ New conversation</button>
      <label htmlFor="search">Search history</label>
      <input id="search" type="search" placeholder="Search titles and messages…" maxLength={200} value={query} onChange={e => setQuery(e.target.value)} />
      <nav aria-label="Conversation history">
        {conversations.map(chat => <button key={chat.id} aria-current={chat.id === active?.id ? 'page' : undefined} disabled={busy} onClick={() => openConversation(chat.id)}>{chat.title}</button>)}
        {!conversations.length && <p className="muted">{query ? 'No matching conversations.' : 'Your conversations will appear here.'}</p>}
      </nav>
      <div className="sidebar-footer">React → FastAPI → selected provider<br/>History stored in PostgreSQL</div>
    </aside>
    <main>
      <header><strong>{active?.title || 'Choose where your answer runs.'}</strong><span className="badge">{provider === 'local' ? 'LOCAL INFERENCE' : 'CLOUD INFERENCE'}</span></header>
      <ProviderPicker provider={provider} onChange={setProvider} busy={busy}/>
      <section className="messages" aria-label="Messages" aria-live="polite">
        {!active?.messages?.length && !pending && <div className="welcome"><div className="symbol">↳</div><h1>Two paths.<br/>Room for ideas.</h1><p>Ask a question to get started. Your chats are saved locally, ready to search and revisit.</p></div>}
        {active?.messages?.map((message, i) => <Message key={i} message={message}/>)}
        {pending && <Message message={{ role: 'user', content: pending }}/>}
        {busy && <div className="thinking" role="status"><span className="spinner" aria-hidden="true"/>{pending ? 'Thinking…' : 'Loading conversation…'}</div>}
        <div ref={bottom}/>
      </section>
      <footer>
        {error && <p className="error" role="alert">{error}</p>}
        <form onSubmit={send}><label className="sr-only" htmlFor="message">Message</label><textarea id="message" placeholder={provider === 'local' ? 'Ask the local model something…' : 'Send a message to ChatGPT…'} maxLength={8000} rows={2} value={draft} disabled={busy} onChange={e => setDraft(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(e); } }}/><button type="submit" disabled={busy || !draft.trim()}>Send ↑</button></form>
        <small>{provider === 'local' ? 'Local model' : 'ChatGPT via Codex · Cloud'} · Enter to send, Shift+Enter for a new line</small>
      </footer>
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(<App/>);
