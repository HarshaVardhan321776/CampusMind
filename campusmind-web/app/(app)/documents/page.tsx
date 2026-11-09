"use client";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { documents as docsApi, Document, ApiError } from "@/lib/api";

function UploadIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="17 8 12 3 7 8"/>
      <line x1="12" y1="3" x2="12" y2="15"/>
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6"/>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
    </svg>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}

function formatSize(bytes?: number) {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const { token } = useAuth();
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = () => {
    if (!token) return;
    docsApi.list(token)
      .then(setDocs)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDocs(); }, [token]);

  const handleUpload = async (file: File) => {
    if (!token) return;
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx"].includes(ext || "")) {
      setUploadError("Only PDF and DOCX files are supported.");
      return;
    }
    setUploading(true);
    setUploadError("");
    setUploadSuccess("");
    try {
      await docsApi.upload(token, file);
      setUploadSuccess(`"${file.name}" uploaded and processed successfully.`);
      fetchDocs();
      setTimeout(() => setUploadSuccess(""), 5000);
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const handleDelete = async (doc: Document) => {
    if (!token) return;
    if (!window.confirm(`Delete "${doc.filename}"? This will also remove its embeddings.`)) return;
    setDeletingId(doc.id);
    try {
      await docsApi.delete(token, doc.id);
      setDocs(prev => prev.filter(d => d.id !== doc.id));
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Delete failed.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-serif font-semibold text-[#1a2744] mb-1">Documents</h1>
        <p className="text-[#64748b]">Upload PDF or DOCX files to build your knowledge base.</p>
      </div>

      {/* Upload area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-10 text-center mb-8 transition-colors ${
          dragOver
            ? "border-[#B9DDF5] bg-[#B9DDF5]/10"
            : "border-[#e2e8f0] bg-white hover:border-[#B9DDF5]"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          className="sr-only"
          id="file-upload"
          aria-label="Upload document"
        />
        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="w-14 h-14 rounded-2xl bg-[#B9DDF5]/30 flex items-center justify-center mx-auto mb-4 text-[#1a2744]">
            {uploading ? (
              <div className="w-6 h-6 border-2 border-[#B9DDF5] border-t-[#1a2744] rounded-full animate-spin" />
            ) : (
              <UploadIcon />
            )}
          </div>
          <p className="text-[#1a2744] font-medium mb-1">
            {uploading ? "Processing document..." : "Drop a file or click to upload"}
          </p>
          <p className="text-sm text-[#94a3b8]">Supports PDF and DOCX — max 50 MB</p>
        </label>

        {!uploading && (
          <button
            onClick={() => fileInputRef.current?.click()}
            className="mt-5 bg-[#FF5A1F] text-white text-sm font-medium px-5 py-2 rounded-lg hover:bg-[#e84f1a] transition-colors"
          >
            Choose File
          </button>
        )}
      </div>

      {/* Feedback messages */}
      {uploadError && (
        <div role="alert" className="mb-4 px-4 py-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
          {uploadError}
        </div>
      )}
      {uploadSuccess && (
        <div role="status" className="mb-4 px-4 py-3 bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg">
          {uploadSuccess}
        </div>
      )}

      {/* Documents list */}
      <div className="bg-white border border-[#e2e8f0] rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[#e2e8f0] flex items-center justify-between">
          <h2 className="font-serif font-semibold text-[#1a2744]">Your Documents</h2>
          <span className="text-sm text-[#94a3b8]">{docs.length} {docs.length === 1 ? "file" : "files"}</span>
        </div>

        {loading ? (
          <div className="divide-y divide-[#f1f5f9]">
            {[1, 2, 3].map(i => (
              <div key={i} className="px-6 py-4 flex items-center gap-4">
                <div className="w-10 h-10 bg-[#f1f5f9] rounded-lg animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-[#f1f5f9] rounded w-48 animate-pulse" />
                  <div className="h-3 bg-[#f1f5f9] rounded w-24 animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        ) : docs.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <p className="text-[#94a3b8] text-sm">No documents uploaded yet. Add your first file above.</p>
          </div>
        ) : (
          <ul className="divide-y divide-[#f1f5f9]" role="list">
            {docs.map((doc) => (
              <li key={doc.id} className="px-6 py-4 flex items-center gap-4 hover:bg-[#f8fafc] transition-colors">
                <div className="w-10 h-10 rounded-lg bg-[#B9DDF5]/20 flex items-center justify-center shrink-0">
                  <span className="text-xs font-mono font-semibold text-[#1a2744] uppercase">
                    {doc.file_type}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#1e293b] truncate">{doc.filename}</p>
                  <p className="text-xs text-[#94a3b8] mt-0.5">Uploaded {formatDate(doc.uploaded_at)}</p>
                </div>
                <div className="shrink-0">
                  <span className="inline-block text-xs bg-green-50 text-green-700 border border-green-200 px-2 py-0.5 rounded font-medium">
                    Indexed
                  </span>
                </div>
                <button
                  onClick={() => handleDelete(doc)}
                  disabled={deletingId === doc.id}
                  className="shrink-0 p-2 text-[#94a3b8] hover:text-red-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors rounded-lg hover:bg-red-50"
                  aria-label={`Delete ${doc.filename}`}
                >
                  {deletingId === doc.id ? (
                    <div className="w-4 h-4 border-2 border-red-300 border-t-red-500 rounded-full animate-spin" />
                  ) : (
                    <TrashIcon />
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

