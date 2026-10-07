import React, { useState, useRef, useEffect } from 'react';
import {
  MessageSquare,
  Send,
  User,
  ShieldCheck,
  AlertCircle,
  Cpu,
  Trash2,
} from 'lucide-react';
import { agentApi } from '../api/agent';
import { PageHeader } from '../components/common/PageHeader';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { extractErrorMessage } from '../api/client';

export function AssistantPage() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am your Nutrino nutrition assistant. I can inspect your daily intake, check your active goals, look up nutritional facts, log consumed meals, or recommend meals tailored to your diet.',
      tools_used: [],
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const quickPrompts = [
    'How many calories have I eaten today?',
    'What is my current goal?',
    'How much nutrition does idli have?',
    'What should I eat for dinner?',
  ];

  const handleSend = async (messageText) => {
    const text = (messageText || input).trim();
    if (!text || loading) return;

    setError('');
    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const data = await agentApi.chatWithAgent(text);
      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response,
        tools_used: data.tools_used || [],
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to obtain response from assistant.'));
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Conversation cleared. How can I help you today?',
        tools_used: [],
        timestamp: new Date(),
      },
    ]);
    setError('');
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200/80">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">AI Nutrition Assistant</h1>
          <p className="text-xs text-slate-500">Conversational interface with deterministic tool execution</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="brand" size="sm" icon={ShieldCheck}>
            Grounded & Deterministic
          </Badge>
          <Button variant="ghost" size="sm" icon={Trash2} onClick={handleClear}>
            Clear
          </Button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <Card className="flex-1 p-4 sm:p-6 border-slate-200/90 overflow-y-auto flex flex-col space-y-4 bg-white/70">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 max-w-3xl ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold ${
                  isUser
                    ? 'bg-slate-800 text-white'
                    : 'bg-emerald-600 text-white shadow-xs'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
              </div>

              <div
                className={`rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                  isUser
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-50 text-slate-800 border border-slate-200/80 shadow-xs'
                }`}
              >
                <div className="whitespace-pre-line font-medium">{msg.content}</div>

                {msg.tools_used?.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-slate-200/60 flex items-center gap-1.5 flex-wrap text-[10px] text-slate-500 font-mono">
                    <Cpu className="w-3 h-3 text-emerald-600" />
                    <span>Tools:</span>
                    {msg.tools_used.map((tool) => (
                      <span key={tool} className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-700">
                        {tool}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-start gap-3 mr-auto max-w-lg">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0">
              <ShieldCheck className="w-4 h-4 animate-pulse" />
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-xs text-slate-500 font-medium flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <span>Analyzing context & querying authoritative tools...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2.5 max-w-lg">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </Card>

      {/* Suggested Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider shrink-0">
          Suggestions:
        </span>
        {quickPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            disabled={loading}
            onClick={() => handleSend(prompt)}
            className="shrink-0 px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors text-[11px]"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-2"
      >
        <input
          type="text"
          placeholder="Ask a nutrition question, check your goals, or describe a meal..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 shadow-sm transition-colors"
        />
        <Button
          type="submit"
          variant="primary"
          size="md"
          loading={loading}
          disabled={!input.trim()}
          icon={Send}
          className="h-11 px-5 rounded-xl shrink-0"
        >
          Send
        </Button>
      </form>
    </div>
  );
}
