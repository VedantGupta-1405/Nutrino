import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { UtensilsCrossed, Send, CheckCircle2, MessageSquare, AlertCircle } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Textarea } from '../common/Textarea';
import { agentApi } from '../../api/agent';
import { extractErrorMessage } from '../../api/client';

export function LogMealModal({ isOpen, onClose }) {
  const queryClient = useQueryClient();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [agentResponse, setAgentResponse] = useState(null);
  const [error, setError] = useState('');

  const examplePrompts = [
    'I had 2 idlis and a bowl of sambar for breakfast',
    '1 bowl cooked toor dal and 1 bowl white rice for lunch',
    '1 plain dosa and 150 ml sambar for dinner',
  ];

  const handleClose = () => {
    setInput('');
    setAgentResponse(null);
    setError('');
    onClose();
  };

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim()) return;

    setError('');
    setLoading(true);

    try {
      const result = await agentApi.chatWithAgent(input.trim());
      setAgentResponse(result);
      // Invalidate queries so dashboard and meals reflect logged data immediately
      queryClient.invalidateQueries({ queryKey: ['today-nutrition'] });
      queryClient.invalidateQueries({ queryKey: ['today-meals'] });
      queryClient.invalidateQueries({ queryKey: ['meals'] });
    } catch (err) {
      setError(extractErrorMessage(err, 'Could not process meal logging request.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Natural-Language Meal Logging"
      description="Describe what you ate in natural language. Nutrino resolves catalog items, portion units, and aggregates nutrition snapshots deterministically."
      maxWidth="lg"
      footer={
        <div className="flex items-center justify-between w-full">
          <Button variant="ghost" size="sm" onClick={handleClose}>
            {agentResponse ? 'Close' : 'Cancel'}
          </Button>
          {!agentResponse ? (
            <Button
              variant="primary"
              size="sm"
              loading={loading}
              disabled={!input.trim()}
              onClick={handleSend}
              icon={Send}
            >
              Log Meal
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setAgentResponse(null);
                setInput('');
              }}
            >
              Log Another Meal
            </Button>
          )}
        </div>
      }
    >
      <div className="space-y-4">
        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span className="leading-relaxed">{error}</span>
          </div>
        )}

        {!agentResponse ? (
          <>
            <form onSubmit={handleSend}>
              <Textarea
                label="What did you eat?"
                placeholder="e.g. I had 2 idlis and a bowl of sambar for breakfast."
                rows={3}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
                required
                autoFocus
              />
            </form>

            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2">
                Quick Example Inputs
              </span>
              <div className="flex flex-col gap-1.5">
                {examplePrompts.map((example) => (
                  <button
                    key={example}
                    type="button"
                    disabled={loading}
                    onClick={() => setInput(example)}
                    className="text-left text-xs px-3 py-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200/60 transition-colors flex items-center justify-between group"
                  >
                    <span>{example}</span>
                    <span className="text-[10px] text-emerald-600 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                      Use
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="space-y-3">
            <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200/80">
              <div className="flex items-center gap-2 text-emerald-800 text-xs font-bold uppercase tracking-wider mb-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Agent Response</span>
              </div>
              <p className="text-xs text-slate-800 leading-relaxed whitespace-pre-line font-medium">
                {agentResponse.response}
              </p>
            </div>

            {agentResponse.tools_used?.length > 0 && (
              <div className="text-[11px] text-slate-500 flex items-center gap-2">
                <span className="font-semibold text-slate-600">Deterministic Operations:</span>
                <span className="font-mono bg-slate-100 px-2 py-0.5 rounded border border-slate-200 text-slate-700">
                  {agentResponse.tools_used.join(', ')}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
