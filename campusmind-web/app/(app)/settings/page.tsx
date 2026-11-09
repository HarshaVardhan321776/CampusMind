"use client";
import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [confirmed, setConfirmed] = useState(false);

  const handleLogout = () => {
    logout();
    router.replace("/auth");
  };

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-serif font-semibold text-[#1a2744] mb-1">Settings</h1>
        <p className="text-[#64748b]">Manage your account and preferences.</p>
      </div>

      {/* Account Info */}
      <div className="bg-white border border-[#e2e8f0] rounded-xl p-6 mb-6">
        <h2 className="font-serif font-semibold text-[#1a2744] mb-4">Account Information</h2>
        <div className="space-y-4">
          <div className="flex items-center gap-4 py-3 border-b border-[#f1f5f9]">
            <div className="w-12 h-12 rounded-xl bg-[#B9DDF5] flex items-center justify-center shrink-0">
              <span className="font-serif font-bold text-[#1a2744] text-lg">
                {user?.name?.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <p className="font-medium text-[#1e293b]">{user?.name}</p>
              <p className="text-sm text-[#64748b]">{user?.email}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm pt-1">
            <div>
              <p className="text-[#94a3b8] text-xs uppercase tracking-wide font-medium mb-1">Account ID</p>
              <p className="text-[#1e293b] font-mono">{user?.id}</p>
            </div>
            <div>
              <p className="text-[#94a3b8] text-xs uppercase tracking-wide font-medium mb-1">Plan</p>
              <p className="text-[#1e293b]">Academic Free</p>
            </div>
          </div>
        </div>
      </div>

      {/* Platform Info */}
      <div className="bg-white border border-[#e2e8f0] rounded-xl p-6 mb-6">
        <h2 className="font-serif font-semibold text-[#1a2744] mb-4">Platform</h2>
        <div className="space-y-3 text-sm">
          {[
            { label: "AI Model", value: "Google Gemini + Groq" },
            { label: "Knowledge Retrieval", value: "RAG (ChromaDB + LangChain)" },
            { label: "Document Formats", value: "PDF, DOCX" },
            { label: "Authentication", value: "JWT (30-day sessions)" },
            { label: "Frontend", value: "Next.js (deployed on Vercel)" },
            { label: "Backend", value: "FastAPI (Python)" },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between py-2 border-b border-[#f8fafc] last:border-0">
              <span className="text-[#64748b]">{label}</span>
              <span className="text-[#1e293b] font-medium">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Legal */}
      <div className="bg-white border border-[#e2e8f0] rounded-xl p-6 mb-6">
        <h2 className="font-serif font-semibold text-[#1a2744] mb-4">Legal</h2>
        <div className="space-y-2">
          <a
            href="/terms"
            className="flex items-center justify-between py-2.5 text-sm text-[#1e293b] hover:text-[#FF5A1F] transition-colors"
          >
            <span>Terms of Service</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </a>
          <a
            href="/privacy"
            className="flex items-center justify-between py-2.5 text-sm text-[#1e293b] hover:text-[#FF5A1F] transition-colors"
          >
            <span>Privacy Policy</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </a>
        </div>
      </div>

      {/* Sign Out */}
      <div className="bg-white border border-[#e2e8f0] rounded-xl p-6">
        <h2 className="font-serif font-semibold text-[#1a2744] mb-2">Sign Out</h2>
        <p className="text-sm text-[#64748b] mb-4">You will be returned to the sign-in page.</p>
        <button
          onClick={handleLogout}
          className="bg-[#FF5A1F] text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-[#e84f1a] transition-colors"
        >
          Sign Out
        </button>
      </div>
    </div>
  );
}

