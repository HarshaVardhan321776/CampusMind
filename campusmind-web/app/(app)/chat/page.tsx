"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { chat as chatApi, documents as docsApi, Conversation, ConversationDetail, Document, ApiError } from "@/lib/api";
import ReactMarkdown from "react-markdown";

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13"/>
      <polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="12" y1="5" x2="12" y2="19"/>
      <line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
  );
}

function CopyIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
  );
}

interface LocalMessage {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export default function ChatPage() {
  const { token } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const convIdParam = searchParams.get("conv");

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load sidebar data
  useEffect(() => {
    if (!token) return;
    Promise.all([chatApi.conversations(token), docsApi.list(token)])
      .then(([convs, docs]) => {
        setConversations(convs);
        setDocuments(docs);
      })
      .catch(console.error);
  }, [token]);

  // Load conversation from URL param
  useEffect(() => {
    if (!token || !convIdParam) return;
    const id = parseInt(convIdParam, 10);
    if (isNaN(id)) return;
    chatApi.conversation(token, id)
      .then((detail: ConversationDetail) => {
        setActiveConvId(id);
        setMessages(detail.messages.map(m => ({
          role: m.role as "user" | "assistant",
          content: m.content,
          sources: m.sources ? m.sources.split(",").filter(Boolean) : [],
        })));
      })
      .catch(console.error);
  }, [token, convIdParam]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const startNew = () => {
    setActiveConvId(null);
    setMessages([]);
    setError("");
    router.push("/chat");
  };

  const loadConversation = (conv: Conversation) => {
    router.push(`/chat?conv=${conv.id}`);
  };

  const handleSend = useCallback(async () => {
    if (!token || !question.trim() || sending) return;
    const q = question.trim();
    setQuestion("");
    setError("");
    setSending(true);

    setMessages(prev => [...prev, { role: "user", content: q }]);

    try {
      const res = await chatApi.ask(token, q, activeConvId ?? undefined, selectedDocId ?? undefined);
      setActiveConvId(res.conversation_id);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: res.answer,
        sources: res.sources,
      }]);
      // Refresh conversation list
      chatApi.conversations(token).then(setConversations).catch(console.error);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to get a response. Please try again.";
      setError(msg);
      setMessages(prev => prev.slice(0, -1)); // remove optimistic user message
      setQuestion(q); // restore
    } finally {
      setSending(false);
    }
  }, [token, question, sending, activeConvId, selectedDocId]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyMessage = (content: string, idx: number) => {
    navigator.clipboard.writeText(content).then(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 2000);
    });
  };

  // Auto-resize textarea
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuestion(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 180) + "px";
    }
  };

  return (
    <div className="flex h-screen">
      {/* Conversation sidebar */}
      <aside className="w-56 bg-white border-r border-[#e2e8f0] flex flex-col shrink-0">
        <div className="p-4 border-b border-[#e2e8f0]">
          <button
            onClick={startNew}
            className="flex items-center gap-2 w-full bg-[#FF5A1F] text-white text-sm font-medium px-3 py-2 rounded-lg hover:bg-[#e84f1a] transition-colors"
          >
            <PlusIcon />
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-2">
          {conversations.length === 0 ? (
            <p className="text-xs text-[#94a3b8] text-center py-6 px-4">No conversations yet</p>
          ) : (
            <ul role="list">
              {conversations.map((conv) => (
                <li key={conv.id}>
                  <button
                    onClick={() => loadConversation(conv)}
                    className={`w-full text-left px-4 py-2.5 text-sm border-b border-[#f8fafc] transition-colors ${
                      activeConvId === conv.id
                        ? "bg-[#B9DDF5]/20 text-[#1a2744] font-medium"
                        : "text-[#64748b] hover:bg-[#f8fafc] hover:text-[#1e293b]"
                    }`}
                  >
                    <span className="block truncate">{conv.title || "Untitled"}</span>
                    <span className="block text-xs text-[#94a3b8] mt-0.5">
                      {new Date(conv.created_at).toLocaleDateString()}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* Chat main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat header */}
        <div className="bg-white border-b border-[#e2e8f0] px-6 py-3 flex items-center gap-4">
          <div className="flex-1 min-w-0">
            <h1 className="font-serif font-semibold text-[#1a2744] text-lg truncate">
              {activeConvId ? "Conversation" : "New Conversation"}
            </h1>
          </div>
          {/* Document selector */}
          {documents.length > 0 && (
            <div className="flex items-center gap-2">
              <label htmlFor="doc-select" className="text-xs text-[#64748b] font-medium shrink-0">
                Context:
              </label>
              <select
                id="doc-select"
                value={selectedDocId ?? ""}
                onChange={(e) => setSelectedDocId(e.target.value ? parseInt(e.target.value, 10) : null)}
                className="text-xs border border-[#e2e8f0] rounded-lg px-2.5 py-1.5 bg-white text-[#1e293b] focus:outline-none focus:border-[#B9DDF5]"
              >
                <option value="">All documents</option>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>{doc.filename}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {messages.length === 0 && !sending && (
            <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto">
              <div className="w-14 h-14 rounded-2xl bg-[#B9DDF5] flex items-center justify-center mb-5">
                <span className="font-serif font-bold text-[#1a2744] text-xl">C</span>
              </div>
              <h2 className="font-serif font-semibold text-[#1a2744] text-xl mb-2">Ask CampusMind</h2>
              <p className="text-sm text-[#64748b] leading-relaxed">
                Ask questions about your uploaded documents, get explanations, summaries, or explore academic topics.
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div className={`max-w-2xl ${msg.role === "user" ? "ml-16" : "mr-16"}`}>
                {msg.role === "user" ? (
                  <div className="bg-[#1a2744] text-white px-4 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed">
                    {msg.content}
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 rounded-md bg-[#B9DDF5] flex items-center justify-center">
                        <span className="font-serif font-bold text-[#1a2744] text-xs">C</span>
                      </div>
                      <span className="text-xs font-medium text-[#64748b]">CampusMind</span>
                    </div>
                    <div className="bg-white border border-[#e2e8f0] rounded-2xl rounded-tl-sm px-5 py-4">
                      <div className="prose-cm text-sm text-[#1e293b]">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-[#e2e8f0]">
                          <p className="text-xs text-[#94a3b8] font-medium mb-1.5">Sources</p>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.sources.map((src, si) => (
                              <span key={si} className="text-xs bg-[#B9DDF5]/20 text-[#1a2744] px-2 py-0.5 rounded font-mono">
                                {src}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      <div className="mt-2 flex justify-end">
                        <button
                          onClick={() => copyMessage(msg.content, idx)}
                          className="text-xs text-[#94a3b8] hover:text-[#64748b] flex items-center gap-1 transition-colors"
                          aria-label="Copy response"
                        >
                          <CopyIcon />
                          {copiedIdx === idx ? "Copied" : "Copy"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Thinking indicator */}
          {sending && (
            <div className="flex justify-start">
              <div className="max-w-2xl mr-16">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded-md bg-[#B9DDF5] flex items-center justify-center">
                    <span className="font-serif font-bold text-[#1a2744] text-xs">C</span>
                  </div>
                  <span className="text-xs font-medium text-[#64748b]">CampusMind</span>
                </div>
                <div className="bg-white border border-[#e2e8f0] rounded-2xl rounded-tl-sm px-5 py-4">
                  <div className="flex items-center gap-1.5">
                    {[0, 1, 2].map(i => (
                      <div
                        key={i}
                        className="w-2 h-2 bg-[#B9DDF5] rounded-full animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Error */}
        {error && (
          <div className="px-6 pb-2">
            <div role="alert" className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2.5">
              {error}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="bg-white border-t border-[#e2e8f0] px-6 py-4">
          <div className="flex items-end gap-3 max-w-3xl mx-auto">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents or any academic topic... (Enter to send, Shift+Enter for new line)"
              rows={1}
              className="flex-1 resize-none border border-[#e2e8f0] rounded-xl px-4 py-3 text-sm text-[#1e293b] placeholder-[#94a3b8] bg-white focus:outline-none focus:border-[#B9DDF5] focus:ring-2 focus:ring-[#B9DDF5]/30 transition-colors leading-relaxed"
              style={{ maxHeight: "180px" }}
              aria-label="Message input"
            />
            <button
              onClick={handleSend}
              disabled={!question.trim() || sending}
              className="bg-[#FF5A1F] text-white p-3 rounded-xl hover:bg-[#e84f1a] disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
              aria-label="Send message"
            >
              <SendIcon />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

