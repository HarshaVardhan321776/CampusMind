"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth as authApi, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function AuthPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        await authApi.register(name, email, password);
        setMode("login");
        setName("");
        setPassword("");
        return;
      }

      const data = await authApi.login(email, password);
      login(data.access_token, data.user);
      router.replace("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-[#e2e8f0] px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{ background: "#1a2744" }}>
            <span className="text-[#B9DDF5] font-serif text-sm font-bold">C</span>
          </div>
          <span className="font-serif font-semibold text-[#1a2744] text-lg tracking-tight">CampusMind</span>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-sm">
          {/* Title */}
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-serif font-semibold text-[#1a2744] mb-2">
              {mode === "login" ? "Welcome back" : "Create your account"}
            </h1>
            <p className="text-sm text-[#64748b]">
              {mode === "login"
                ? "Sign in to your academic workspace"
                : "Start your academic AI journey"}
            </p>
          </div>

          {/* Card */}
          <div className="bg-white border border-[#e2e8f0] rounded-xl p-8 shadow-sm">
            {/* Tab switcher */}
            <div className="flex border border-[#e2e8f0] rounded-lg p-1 mb-6">
              <button
                type="button"
                onClick={() => { setMode("login"); setError(""); }}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                  mode === "login"
                    ? "bg-[#B9DDF5] text-[#1a2744]"
                    : "text-[#64748b] hover:text-[#1a2744]"
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => { setMode("register"); setError(""); }}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                  mode === "register"
                    ? "bg-[#B9DDF5] text-[#1a2744]"
                    : "text-[#64748b] hover:text-[#1a2744]"
                }`}
              >
                Register
              </button>
            </div>

            <form onSubmit={handleSubmit} noValidate>
              {/* Error */}
              {error && (
                <div
                  role="alert"
                  className="mb-4 px-3 py-2.5 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg"
                >
                  {error}
                </div>
              )}

              {/* Name (register only) */}
              {mode === "register" && (
                <div className="mb-4">
                  <label htmlFor="name" className="block text-sm font-medium text-[#1e293b] mb-1.5">
                    Full Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    autoComplete="name"
                    placeholder="Alex Johnson"
                    className="w-full border border-[#e2e8f0] rounded-lg px-3.5 py-2.5 text-sm text-[#1e293b] placeholder-[#94a3b8] bg-white focus:outline-none focus:border-[#B9DDF5] focus:ring-2 focus:ring-[#B9DDF5]/30 transition-colors"
                  />
                </div>
              )}

              {/* Email */}
              <div className="mb-4">
                <label htmlFor="email" className="block text-sm font-medium text-[#1e293b] mb-1.5">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete={mode === "login" ? "email" : "new-email"}
                  placeholder="you@university.edu"
                  className="w-full border border-[#e2e8f0] rounded-lg px-3.5 py-2.5 text-sm text-[#1e293b] placeholder-[#94a3b8] bg-white focus:outline-none focus:border-[#B9DDF5] focus:ring-2 focus:ring-[#B9DDF5]/30 transition-colors"
                />
              </div>

              {/* Password */}
              <div className="mb-6">
                <label htmlFor="password" className="block text-sm font-medium text-[#1e293b] mb-1.5">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  placeholder="········"
                  className="w-full border border-[#e2e8f0] rounded-lg px-3.5 py-2.5 text-sm text-[#1e293b] placeholder-[#94a3b8] bg-white focus:outline-none focus:border-[#B9DDF5] focus:ring-2 focus:ring-[#B9DDF5]/30 transition-colors"
                />
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#FF5A1F] text-white font-medium py-2.5 px-4 rounded-lg text-sm transition-colors hover:bg-[#e84f1a] disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    {mode === "login" ? "Signing in..." : "Creating account..."}
                  </>
                ) : (
                  mode === "login" ? "Sign In" : "Create Account"
                )}
              </button>
            </form>
          </div>

          {/* Legal */}
          <p className="text-center text-xs text-[#94a3b8] mt-6">
            By continuing, you agree to our{" "}
            <a href="/terms" className="text-[#64748b] underline underline-offset-2 hover:text-[#1a2744]">Terms of Service</a>
            {" "}and{" "}
            <a href="/privacy" className="text-[#64748b] underline underline-offset-2 hover:text-[#1a2744]">Privacy Policy</a>
          </p>
        </div>
      </main>
    </div>
  );
}

