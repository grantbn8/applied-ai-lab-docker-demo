import React from 'react';
import Markdown from 'react-markdown';

export default function Message({ message }) {
  return <article className={`message ${message.role}`}>
    <h2 className="message-author">{message.role === 'user' ? 'You' : message.provider === 'chatgpt' ? 'ChatGPT · Cloud' : 'Ollama · Local'}</h2>
    {message.role === 'assistant'
      ? <div className="markdown"><Markdown skipHtml>{message.content}</Markdown></div>
      : <p className="user-text">{message.content}</p>}
  </article>;
}
