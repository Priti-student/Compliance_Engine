import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

function BrandMark() {
  return <div className="relative h-11 w-16" aria-hidden="true"><span className="absolute left-0 top-1 h-10 w-10 rounded-full bg-[#b6e878]/90" /><span className="absolute left-6 top-1 h-10 w-10 rounded-full bg-[#16a56d]/90" /></div>;
}

function UserIcon() {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><circle cx="12" cy="7" r="3.5" /><path strokeLinecap="round" d="M4.5 20a7.5 7.5 0 0 1 15 0" /></svg>;
}

function LockIcon() {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><rect x="5" y="10" width="14" height="10" rx="2" /><path strokeLinecap="round" d="M8.5 10V7a3.5 3.5 0 0 1 7 0v3M12 14v2" /></svg>;
}

function EyeIcon({ visible }: { visible: boolean }) {
  return visible ? <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M2.5 12S6 5 12 5s9.5 7 9.5 7-3.5 7-9.5 7S2.5 12 2.5 12Z" /><circle cx="12" cy="12" r="2.7" /></svg> : <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M3 3l18 18M10.6 10.7a2 2 0 0 0 2.7 2.7M9.9 5.1A10.7 10.7 0 0 1 12 4.9c5 0 8.5 4.2 9.5 7.1a11.7 11.7 0 0 1-3 4.2M6.2 6.2C4.4 7.7 3.2 10 2.5 12c.7 2 2.1 4.4 4.2 5.9A10.7 10.7 0 0 0 12 19.1c.9 0 1.8-.1 2.7-.4" /></svg>;
}

export default function LoginPage() {
  const { user, ready, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (!ready) return <div className="flex min-h-screen items-center justify-center bg-[#092d23] text-sm text-white/80">Loading…</div>;
  if (user) return <Navigate to={location.state?.from || "/"} replace />;

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError("");
    try { await login(username, password); navigate(location.state?.from || "/", { replace: true }); }
    catch (err) { setError(err instanceof Error ? err.message : "Login failed"); }
    finally { setBusy(false); }
  };

  return <main className="login-scene min-h-screen bg-[#092d23] text-slate-900">
    <div className="login-scene__shade absolute inset-0" />
    <header className="absolute left-0 top-0 z-10 flex items-center px-7 py-8 sm:px-12 sm:py-10">
      <BrandMark /><div><h1 className="text-[29px] font-bold leading-none tracking-tight text-white">Legal<span className="text-[#48ce8d]">Vision</span></h1><p className="mt-2 text-[9px] font-semibold tracking-[0.26em] text-white/75 sm:text-[10px]">COMPLIANCE | ACCURACY | CONSUMER TRUST</p></div>
    </header>
    <section className="absolute left-7 top-1/2 z-10 hidden -translate-y-1/2 text-white sm:left-[22.5%] lg:block"><p className="text-sm font-medium tracking-[0.48em] text-white/85">SAFE PRODUCTS</p><p className="mt-2 text-sm font-medium tracking-[0.48em] text-white/85">HAPPIER CONSUMERS</p><div className="mt-5 h-[3px] w-14 bg-[#b6e878]" /></section>
    <section className="relative z-10 flex min-h-screen items-center justify-center px-5 py-28 sm:justify-end sm:px-12 lg:px-[7.5vw]"><div className="w-full max-w-[490px] rounded-[20px] border border-white/70 bg-[#fbfbfd]/[0.97] px-7 py-7 shadow-[0_25px_70px_rgba(0,0,0,0.25)] sm:px-10 sm:py-7">
      <div className="text-center"><div className="mx-auto flex items-center justify-center gap-5 text-[#07563c]"><span className="h-px w-16 bg-slate-300" /><svg className="h-16 w-16" viewBox="0 0 64 70" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true"><path d="M32 3 54 12v18c0 16-9.5 29.5-22 36C19.5 59.5 10 46 10 30V12L32 3Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M23 23h15v18H23zM27 28h7m-7 5h10m-10 5h8" /></svg><span className="h-px w-16 bg-slate-300" /></div><h2 className="mt-3 text-3xl font-bold tracking-tight text-[#10223a] sm:text-[39px]">Welcome Back</h2><p className="mt-1 text-xl text-slate-500 sm:text-2xl">Sign in to <span className="font-bold text-[#076a47]">LegalVision</span></p><div className="mx-auto mt-4 h-[3px] w-10 bg-[#06734c]" /></div>
      <form onSubmit={onSubmit} className="mt-6 space-y-4"><div><label htmlFor="username" className="mb-2 block text-sm font-semibold text-slate-800">Username</label><div className="relative"><span className="pointer-events-none absolute inset-y-0 left-0 flex w-14 items-center justify-center text-slate-700"><UserIcon /></span><input id="username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Enter your username" autoComplete="username" required className="login-input pl-14" /></div></div>
        <div><label htmlFor="password" className="mb-2 block text-sm font-semibold text-slate-800">Password</label><div className="relative"><span className="pointer-events-none absolute inset-y-0 left-0 flex w-14 items-center justify-center text-slate-700"><LockIcon /></span><input id="password" type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" autoComplete="current-password" required className="login-input pl-14 pr-14" /><button type="button" onClick={() => setShowPassword((shown) => !shown)} className="absolute inset-y-0 right-0 flex w-14 items-center justify-center text-slate-700 transition hover:text-[#06734c]" aria-label={showPassword ? "Hide password" : "Show password"}><EyeIcon visible={showPassword} /></button></div></div>
        {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}<button type="submit" disabled={busy} className="mt-7 flex w-full items-center justify-center gap-4 rounded-lg bg-[#075a3f] px-4 py-3 text-base font-medium text-white shadow-md transition hover:bg-[#064b35] focus:outline-none focus:ring-4 focus:ring-[#15966a]/30 disabled:cursor-not-allowed disabled:opacity-60">{busy ? "Signing in…" : "Sign in"}{!busy && <span aria-hidden="true" className="text-2xl leading-none">→</span>}</button>
      </form><footer className="mt-6 border-t border-slate-200 pt-4 text-center text-xs text-slate-500">© 2026 LegalVision. All rights reserved.</footer>
    </div></section>
  </main>;
}
