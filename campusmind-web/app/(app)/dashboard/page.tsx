"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { documents as docsApi, chat as chatApi, Document, Conversation } from "@/lib/api";
import Link from "next/link";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function DashboardPage() {
  const { user, token } = useAuth();
  const [docs, setDocs] = useState<Document[]>([]);
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    Promise.all([docsApi.list(token), chatApi.conversations(token)])
      .then(([d, c]) => {
        setDocs(d.slice(0, 5));
        setConvs(c.slice(0, 5));
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Welcome */}
      <div className="mb-10">
        <h1 className="text-3xl font-serif font-semibold text-[#1a2744] mb-1">
          {greeting()}, {user?.name?.split(" ")[0]}.
        </h1>
        <p className="text-[#64748b] text-base">
          Your academic workspace is ready.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
        <Link
          href="/chat"
          className="group border border-[#e2e8f0] bg-white rounded-xl p-6 hover:border-[#B9DDF5] hover:shadow-sm transition-all"
        >
          <div className="w-10 h-10 rounded-lg bg-[#B9DDF5] flex items-center justify-center mb-4">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a2744" strokeWidth="1.75">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <h2 className="font-serif font-semibold text-[#1a2744] text-lg mb-1">Start a Conversation</h2>
          <p className="text-sm text-[#64748b]">Ask questions about your documents or any academic topic.</p>
        </Link>

        <Link
          href="/documents"
          className="group border border-[#e2e8f0] bg-white rounded-xl p-6 hover:border-[#B9DDF5] hover:shadow-sm transition-all"
        >
          <div className="w-10 h-10 rounded-lg bg-[#FF5A1F]/10 flex items-center justify-center mb-4">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FF5A1F" strokeWidth="1.75">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <h2 className="font-serif font-semibold text-[#1a2744] text-lg mb-1">Upload a Document</h2>
          <p className="text-sm text-[#64748b]">Add PDF or DOCX files to your knowledge base.</p>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        {[
          { label: "Documents", value: loading ? "—" : docs.length.toString(), note: "in your library" },
          { label: "Conversations", value: loading ? "—" : convs.length.toString(), note: "total chats" },
          { label: "AI Model", value: "Gemini", note: "powered by Google" },
          { label: "RAG", value: "Active", note: "document retrieval" },
        ].map((s) => (
          <div key={s.label} className="bg-white border border-[#e2e8f0] rounded-xl px-5 py-4">
            <p className="text-xs text-[#94a3b8] uppercase tracking-wide font-medium mb-1">{s.label}</p>
            <p className="text-2xl font-serif font-semibold text-[#1a2744] mb-0.5">{s.value}</p>
            <p className="text-xs text-[#64748b]">{s.note}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recent Documents */}
        <div className="bg-white border border-[#e2e8f0] rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-serif font-semibold text-[#1a2744]">Recent Documents</h2>
            <Link href="/documents" className="text-xs text-[#FF5A1F] font-medium hover:underline">View all</Link>
          </div>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-10 bg-[#f8fafc] rounded-lg animate-pulse" />
              ))}
            </div>
          ) : docs.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-[#94a3b8]">No documents yet.</p>
              <Link href="/documents" className="mt-2 inline-block text-sm text-[#FF5A1F] font-medium hover:underline">
                Upload your first document
              </Link>
            </div>
          ) : (
            <ul className="space-y-2" role="list">
              {docs.map((doc) => (
                <li key={doc.id} className="flex items-center gap-3 py-2 border-b border-[#f1f5f9] last:border-0">
                  <div className="w-8 h-8 rounded-md bg-[#B9DDF5]/30 flex items-center justify-center shrink-0">
                    <span className="text-[10px] font-mono font-medium text-[#1a2744] uppercase">{doc.file_type}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-[#1e293b] font-medium truncate">{doc.filename}</p>
                    <p className="text-xs text-[#94a3b8]">{formatDate(doc.uploaded_at)}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Recent Conversations */}
        <div className="bg-white border border-[#e2e8f0] rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-serif font-semibold text-[#1a2744]">Recent Conversations</h2>
            <Link href="/chat" className="text-xs text-[#FF5A1F] font-medium hover:underline">View all</Link>
          </div>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-10 bg-[#f8fafc] rounded-lg animate-pulse" />
              ))}
            </div>
          ) : convs.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-[#94a3b8]">No conversations yet.</p>
              <Link href="/chat" className="mt-2 inline-block text-sm text-[#FF5A1F] font-medium hover:underline">
                Start your first chat
              </Link>
            </div>
          ) : (
            <ul className="space-y-2" role="list">
              {convs.map((conv) => (
                <li key={conv.id}>
                  <Link
                    href={`/chat?conv=${conv.id}`}
                    className="flex items-center gap-3 py-2 border-b border-[#f1f5f9] last:border-0 hover:text-[#FF5A1F] transition-colors"
                  >
                    <div className="w-8 h-8 rounded-md bg-[#f1f5f9] flex items-center justify-center shrink-0">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="1.75">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-[#1e293b] font-medium truncate">
                        {conv.title || "Untitled conversation"}
                      </p>
                      <p className="text-xs text-[#94a3b8]">{formatDate(conv.created_at)}</p>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

