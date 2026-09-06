import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  X,
  Send,
  RefreshCw,
  Trash2,
  Wifi,
  WifiOff,
  Sparkles,
  ExternalLink,
  BookOpen,
  HelpCircle,
  Zap,
} from 'lucide-react';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { sendChatMessage } from '../services/api';
import { getKnowledgeFromLocal, queryLocalKnowledgeBase } from '../services/knowledgeDB';

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const { isOnline, networkState, lastSyncTime, triggerSync } = useNetworkStatus();
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'bot',
      text: "👋 Hello! I am **LunarVision Assistant**, your offline-first lunar surface registration helper.\n\nI can answer questions about our computer vision pipeline (SIFT, AKAZE, RANSAC, SSIM), interpret metrics, or reference built-in ISRO Chandrayaan mission notes.",
      mode: 'offline',
      source: 'System Initializer',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      suggestedQuestions: [
        'What is LunarVision?',
        'How does image matching work?',
        'What is RANSAC?',
        'Explain OHRC, TMC and IIRS',
        'What is the latest lunar news?',
      ],
    },
  ]);

  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (queryText) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend || !textToSend.trim() || isLoading) return;

    const userMsgId = `user-${Date.now()}`;
    const userMsg = {
      id: userMsgId,
      sender: 'user',
      text: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputQuery('');
    setIsLoading(true);

    let botResponse = null;

    if (isOnline) {
      // ONLINE MODE: Call Backend Endpoint
      try {
        botResponse = await sendChatMessage(userMsg.text, true);
      } catch (err) {
        console.warn('Backend query failed, reverting to local KB:', err);
      }
    }

    // OFFLINE MODE or Fallback if backend failed
    if (!botResponse || botResponse.source === 'Client Fallback') {
      try {
        // Try local backend call with is_online=false
        botResponse = await sendChatMessage(userMsg.text, false);
      } catch (e) {
        // Ultimate client-side fallback via IndexedDB
        const localKB = await getKnowledgeFromLocal();
        const clientRes = queryLocalKnowledgeBase(localKB, userMsg.text);
        botResponse = {
          answer: clientRes.answer,
          mode: 'offline',
          source: 'IndexedDB Client Knowledge Base',
          citations: [],
          confidence: 0.9,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          suggested_questions: clientRes.suggested_questions,
        };
      }
    }

    const botMsg = {
      id: `bot-${Date.now()}`,
      sender: 'bot',
      text: botResponse.answer,
      mode: botResponse.mode || (isOnline ? 'online' : 'offline'),
      source: botResponse.source || 'LunarVision Engine',
      citations: botResponse.citations || [],
      confidence: botResponse.confidence,
      timestamp: botResponse.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      suggestedQuestions: botResponse.suggested_questions || [
        'What is RANSAC?',
        'What is Lowe\'s ratio test?',
        'Explain OHRC, TMC and IIRS',
      ],
    };

    setMessages((prev) => [...prev, botMsg]);
    setIsLoading(false);
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome-reset',
        sender: 'bot',
        text: 'Chat history cleared. How can I assist you with LunarVision or ISRO missions?',
        mode: isOnline ? 'online' : 'offline',
        source: 'System Reset',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggestedQuestions: [
          'What is LunarVision?',
          'What is RANSAC?',
          'Explain OHRC, TMC and IIRS',
          'What is the latest lunar news?',
        ],
      },
    ]);
  };

  // Status Badge Component
  const renderStatusBadge = () => {
    if (networkState === 'RECONNECTING') {
      return (
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-medium animate-pulse">
          <RefreshCw className="w-3 h-3 animate-spin text-amber-400" />
          <span>🟡 Reconnecting...</span>
        </div>
      );
    }
    if (networkState === 'UPDATED') {
      return (
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-medium">
          <Wifi className="w-3 h-3 text-emerald-400" />
          <span>✓ Knowledge updated</span>
        </div>
      );
    }
    if (isOnline) {
      return (
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-medium">
          <Wifi className="w-3 h-3 text-emerald-400" />
          <span>🟢 Online — Knowledge Current</span>
        </div>
      );
    }
    return (
      <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs font-medium">
        <WifiOff className="w-3 h-3 text-rose-400" />
        <span>🔴 Offline — Local Knowledge</span>
      </div>
    );
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Floating Action Button (FAB) */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="relative group flex items-center space-x-2 bg-gradient-to-r from-cyan-600 via-teal-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white px-4 py-3.5 rounded-2xl shadow-2xl transition-all duration-300 transform hover:scale-105 border border-cyan-400/40 focus:outline-none"
        >
          <div className="relative">
            <MessageSquare className="w-6 h-6 text-white" />
            <span
              className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-slate-900 ${
                isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
              }`}
            />
          </div>
          <span className="font-semibold text-sm tracking-wide hidden sm:inline">
            LunarVision Assistant
          </span>
          <span
            className={`text-[10px] font-mono px-1.5 py-0.5 rounded border uppercase ${
              isOnline
                ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300'
                : 'bg-rose-950/80 border-rose-500/50 text-rose-300'
            }`}
          >
            {isOnline ? 'Online' : 'Offline'}
          </span>
        </button>
      )}

      {/* Main Chat Panel */}
      {isOpen && (
        <div className="w-[92vw] sm:w-[420px] h-[580px] max-h-[85vh] bg-slate-950/95 backdrop-blur-xl border border-cyan-500/30 rounded-3xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300">
          {/* Header */}
          <div className="bg-slate-900/90 border-b border-cyan-900/40 p-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg border border-cyan-300/40">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="font-bold text-slate-100 text-base">LunarVision Assistant</h3>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-500/30 text-cyan-300">
                    v1.0
                  </span>
                </div>
                <div className="mt-0.5">{renderStatusBadge()}</div>
              </div>
            </div>

            <div className="flex items-center space-x-1">
              <button
                onClick={handleClearChat}
                title="Clear Chat History"
                className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800/80 transition"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                title="Close Chat"
                className="p-1.5 text-slate-400 hover:text-slate-100 rounded-lg hover:bg-slate-800/80 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Last Sync Info Bar */}
          {lastSyncTime && (
            <div className="bg-cyan-950/40 border-b border-cyan-900/30 py-1 px-4 flex items-center justify-between text-[11px] text-cyan-300/80 font-mono">
              <span>Last Updated: {lastSyncTime}</span>
              <span>ISRO KB Synced</span>
            </div>
          )}

          {/* Messages Transcript */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-slate-950 via-slate-900/50 to-slate-950">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.sender === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div
                  className={`max-w-[88%] rounded-2xl p-3.5 text-sm shadow-md transition-all ${
                    msg.sender === 'user'
                      ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-br-none border border-cyan-400/30'
                      : 'bg-slate-900/90 text-slate-200 border border-slate-800 rounded-bl-none'
                  }`}
                >
                  {/* Mode / Source indicator for bot */}
                  {msg.sender === 'bot' && (
                    <div className="flex items-center justify-between text-[10px] font-mono text-cyan-400/90 border-b border-slate-800 pb-1.5 mb-2">
                      <span className="flex items-center space-x-1">
                        {msg.mode === 'online' ? (
                          <Wifi className="w-3 h-3 text-emerald-400 inline" />
                        ) : (
                          <WifiOff className="w-3 h-3 text-amber-400 inline" />
                        )}
                        <span className="capitalize">{msg.mode || 'offline'} Mode</span>
                      </span>
                      <span className="text-slate-400">{msg.source}</span>
                    </div>
                  )}

                  {/* Body Text */}
                  <div className="whitespace-pre-wrap leading-relaxed">
                    {msg.text}
                  </div>

                  {/* Citations block */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-slate-800 space-y-1">
                      <div className="text-[11px] font-semibold text-cyan-400 flex items-center space-x-1">
                        <BookOpen className="w-3 h-3" />
                        <span>Sources & References:</span>
                      </div>
                      {msg.citations.map((cite, idx) => (
                        <a
                          key={idx}
                          href={cite.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[11px] text-cyan-300/80 hover:text-cyan-200 flex items-center space-x-1 underline truncate"
                        >
                          <ExternalLink className="w-2.5 h-2.5 flex-shrink-0" />
                          <span className="truncate">{cite.title}</span>
                        </a>
                      ))}
                    </div>
                  )}

                  <div className="mt-1.5 text-[10px] text-slate-400 text-right font-mono">
                    {msg.timestamp}
                  </div>
                </div>

                {/* Suggested Questions */}
                {msg.sender === 'bot' && msg.suggestedQuestions && (
                  <div className="mt-2.5 flex flex-wrap gap-1.5 max-w-[92%]">
                    {msg.suggestedQuestions.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSend(q)}
                        className="text-xs bg-slate-900/80 hover:bg-cyan-950 hover:border-cyan-500/60 text-cyan-300/90 border border-cyan-900/40 rounded-xl px-2.5 py-1 transition flex items-center space-x-1"
                      >
                        <Zap className="w-3 h-3 text-cyan-400" />
                        <span>{q}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center space-x-2 text-cyan-400 bg-slate-900/80 border border-slate-800 p-3 rounded-2xl w-fit">
                <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
                <span className="text-xs font-mono">Analyzing question & knowledge base...</span>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Footer Input Area */}
          <div className="p-3 bg-slate-900/95 border-t border-slate-800/80">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center space-x-2"
            >
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder={
                  isOnline
                    ? "Ask about LunarVision, RANSAC, or ISRO news..."
                    : "Ask questions (Offline KB Mode active)..."
                }
                className="flex-1 bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-400 focus:outline-none transition"
              />
              <button
                type="submit"
                disabled={!inputQuery.trim() || isLoading}
                className="p-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white transition shadow-md"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
            <div className="mt-2 text-[10px] text-center text-slate-400 flex items-center justify-center space-x-2 font-mono">
              <span>Offline-First System</span>
              <span>•</span>
              <span>Built-in Reference Library</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
