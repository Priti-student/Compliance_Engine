import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function LoginPage() {
  const { user, ready, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#061633]">
        <div className="text-sm text-blue-200 animate-pulse">
          Loading…
        </div>
      </div>
    );
  }

  if (user) {
    return <Navigate to={location.state?.from || "/"} replace />;
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");

    try {
      await login(username, password);
      navigate(location.state?.from || "/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-white">

      {/* ================= MAIN SPLIT SCREEN ================= */}
      <div className="min-h-screen lg:grid lg:grid-cols-2">

        {/* =====================================================
            LEFT SIDE - NAVY DESIGN
        ====================================================== */}
        <section className="relative hidden overflow-hidden bg-[#061B41] lg:flex">

          {/* Background circles */}
          <div className="absolute -left-32 -top-32 h-80 w-80 rounded-full border border-blue-400/20 bg-blue-500/10" />

          <div className="absolute -right-40 -top-40 h-[500px] w-[500px] rounded-full border border-blue-400/10 bg-blue-500/10" />

          <div className="absolute bottom-[-180px] left-[-150px] h-[430px] w-[430px] rounded-full bg-blue-600/20" />

          <div className="absolute bottom-[-250px] right-[-180px] h-[550px] w-[550px] rounded-full border border-blue-400/20 bg-blue-500/10" />

          {/* Small circles */}
          <div className="absolute left-[62%] top-[26%] h-3 w-3 rounded-full bg-blue-400/70" />

          <div className="absolute right-[12%] top-[48%] h-5 w-5 rounded-full bg-blue-400/40" />

          <div className="absolute left-[55%] bottom-[18%] h-4 w-4 rounded-full bg-blue-400/50" />

          <div className="absolute right-[28%] bottom-[10%] h-2 w-2 rounded-full bg-white/50" />

          {/* Dotted pattern */}
          <div className="absolute right-12 top-28 grid grid-cols-5 gap-4 opacity-30">
            {Array.from({ length: 25 }).map((_, index) => (
              <span
                key={index}
                className="h-1 w-1 rounded-full bg-blue-300"
              />
            ))}
          </div>

          {/* Left content */}
          <div className="relative z-10 flex min-h-screen w-full flex-col px-12 py-10 xl:px-16">

            {/* Logo */}
            <div className="flex items-center gap-3">

              {/* Logo circles */}
              <div className="relative h-10 w-10">
                <div className="absolute left-0 top-1 h-8 w-8 rounded-full bg-blue-300" />
                <div className="absolute left-3 top-1 h-8 w-8 rounded-full bg-blue-500/90" />
              </div>

              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  Legal<span className="text-blue-400">Vision</span>
                </h1>

                <p className="mt-1 text-[10px] font-medium uppercase tracking-[0.25em] text-blue-200/70">
                  Compliance • Accuracy • Consumer Trust
                </p>
              </div>
            </div>

            {/* Small line */}
            <div className="mt-7 h-1 w-12 rounded-full bg-blue-400" />

            {/* Main heading */}
            <div className="mt-20 max-w-xl">

              <h2 className="text-5xl font-bold leading-[1.08] tracking-tight text-white xl:text-5xl">
                Scan. Verify.
                <span className="mt-2 block text-blue-400">
                  Ensure Compliance.
                </span>
              </h2>

              <p className="mt-7 max-w-lg text-base leading-7 text-blue-100/75 xl:text-lg">
                AI-powered compliance checking for packaged commodities
                under the Legal Metrology (Packaged Commodities)
                Rules, 2011.
              </p>

            </div>

            {/* Features */}
            <div className="mt-12 space-y-6">

              {/* Feature 1 */}
              <div className="flex items-center gap-5">

                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border border-blue-400/40 bg-blue-500/15">
                  <svg
                    className="h-7 w-7 text-blue-300"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.7"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M4 8V6a2 2 0 012-2h2M20 8V6a2 2 0 00-2-2h-2M4 16v2a2 2 0 002 2h2M20 16v2a2 2 0 01-2 2h-2"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M7 10h10M7 14h10"
                    />
                  </svg>
                </div>

                <div>
                  <h3 className="font-semibold text-white">
                    Scan Products
                  </h3>

                  <p className="mt-1 text-sm text-blue-200/60">
                    Extract label information
                  </p>
                </div>

              </div>

              {/* Feature 2 */}
              <div className="flex items-center gap-5">

                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border border-blue-400/40 bg-blue-500/15">
                  <svg
                    className="h-7 w-7 text-blue-300"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.7"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 3l7 4v5c0 4.5-3 7.8-7 9-4-1.2-7-4.5-7-9V7l7-4z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 12l2 2 4-4"
                    />
                  </svg>
                </div>

                <div>
                  <h3 className="font-semibold text-white">
                    Check Compliance
                  </h3>

                  <p className="mt-1 text-sm text-blue-200/60">
                    Validate with LMPC Rules
                  </p>
                </div>

              </div>

              {/* Feature 3 */}
              <div className="flex items-center gap-5">

                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border border-blue-400/40 bg-blue-500/15">
                  <svg
                    className="h-7 w-7 text-blue-300"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.7"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M4 19V9"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M10 19V5"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M16 19v-7"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M22 19V3"
                    />
                  </svg>
                </div>

                <div>
                  <h3 className="font-semibold text-white">
                    Get Insights
                  </h3>

                  <p className="mt-1 text-sm text-blue-200/60">
                    Detailed reports and analytics
                  </p>
                </div>

              </div>

            </div>

            {/* Bottom tagline */}
            <div className="mt-auto pt-10">

              <div className="mb-4 h-1 w-12 rounded-full bg-blue-400" />

              <p className="text-[11px] uppercase tracking-[0.28em] text-blue-200/60">
                Safer Products • Stronger Consumers
              </p>

            </div>

          </div>
        </section>


        {/* =====================================================
            RIGHT SIDE - LOGIN
        ====================================================== */}
        <section className="relative flex min-h-screen items-center justify-center overflow-hidden bg-white px-5 py-10 sm:px-8">

          {/* Decorative circles */}
          <div className="absolute -right-32 -top-32 h-72 w-72 rounded-full bg-blue-50" />

          <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full border border-blue-100" />

          <div className="absolute right-10 top-20 h-4 w-4 rounded-full bg-blue-300" />

          <div className="absolute bottom-24 left-16 h-3 w-3 rounded-full bg-blue-400/60" />

          {/* Login wrapper */}
          <div className="relative z-10 w-full max-w-md">

            {/* Mobile Logo */}
            <div className="mb-8 flex items-center gap-3 lg:hidden">

              <div className="relative h-10 w-10">
                <div className="absolute left-0 top-1 h-8 w-8 rounded-full bg-blue-200" />
                <div className="absolute left-3 top-1 h-8 w-8 rounded-full bg-blue-500" />
              </div>

              <div>
                <h1 className="text-2xl font-bold text-[#09265A]">
                  Legal<span className="text-blue-500">Vision</span>
                </h1>

                <p className="text-[10px] uppercase tracking-wider text-slate-400">
                  Compliance Intelligence
                </p>
              </div>

            </div>

            {/* Login Card */}
            <div className="rounded-3xl border border-blue-100 bg-white p-7 shadow-[0_20px_60px_rgba(9,38,90,0.10)] sm:p-9">

              {/* Heading */}
              <div className="mb-8">

                <p className="mb-3 text-xs font-semibold uppercase tracking-[0.3em] text-blue-500">
                  Welcome Back
                </p>

                <h2 className="text-3xl font-bold tracking-tight text-[#09265A] sm:text-4xl">
                  Sign in to LegalVision
                </h2>

                <p className="mt-3 text-sm text-slate-500">
                  Access your compliance dashboard
                </p>

              </div>


              {/* Form */}
              <form onSubmit={onSubmit} className="space-y-5">

                {/* Username */}
                <div>

                  <label
                    htmlFor="username"
                    className="mb-2 block text-sm font-semibold text-[#09265A]"
                  >
                    Username
                  </label>

                  <div className="relative">

                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
                      <svg
                        className="h-5 w-5 text-slate-400"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M20 21a8 8 0 00-16 0"
                        />

                        <circle cx="12" cy="7" r="4" />
                      </svg>
                    </div>

                    <input
                      id="username"
                      className="w-full rounded-xl border border-blue-100 bg-slate-50 py-3.5 pl-12 pr-4 text-sm text-[#09265A] outline-none transition-all placeholder:text-slate-400 hover:border-blue-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Enter your username"
                      autoComplete="username"
                      required
                    />

                  </div>

                </div>


                {/* Password */}
                <div>

                  <label
                    htmlFor="password"
                    className="mb-2 block text-sm font-semibold text-[#09265A]"
                  >
                    Password
                  </label>

                  <div className="relative">

                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">

                      <svg
                        className="h-5 w-5 text-slate-400"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                      >
                        <rect
                          x="4"
                          y="10"
                          width="16"
                          height="11"
                          rx="2"
                        />

                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M8 10V7a4 4 0 018 0v3"
                        />
                      </svg>

                    </div>

                    <input
                      id="password"
                      className="w-full rounded-xl border border-blue-100 bg-slate-50 py-3.5 pl-12 pr-4 text-sm text-[#09265A] outline-none transition-all placeholder:text-slate-400 hover:border-blue-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      autoComplete="current-password"
                      required
                    />

                  </div>

                </div>


                {/* Error */}
                {error && (
                  <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3">

                    <p className="text-sm text-red-600">
                      {error}
                    </p>

                  </div>
                )}


                {/* Sign In */}
                <button
                  type="submit"
                  disabled={busy}
                  className="group flex w-full items-center justify-center gap-2 rounded-xl bg-[#0B3B82] px-4 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-900/20 transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#0A4B9B] hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
                >

                  {busy ? (
                    <>
                      <svg
                        className="h-5 w-5 animate-spin"
                        viewBox="0 0 24 24"
                        fill="none"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="9"
                          stroke="currentColor"
                          strokeWidth="3"
                        />

                        <path
                          className="opacity-90"
                          fill="currentColor"
                          d="M21 12a9 9 0 01-9 9v-3a6 6 0 006-6h3z"
                        />
                      </svg>

                      Signing in…
                    </>
                  ) : (
                    <>
                      Sign in

                      <svg
                        className="h-5 w-5 transition-transform duration-200 group-hover:translate-x-1"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M5 12h14M13 6l6 6-6 6"
                        />
                      </svg>
                    </>
                  )}

                </button>


                {/* Divider */}
                {/* <div className="flex items-center gap-4 py-1">

                  <div className="h-px flex-1 bg-slate-200" />

                  <span className="text-xs text-slate-400">
                    or
                  </span>

                  <div className="h-px flex-1 bg-slate-200" />

                </div> */}


                {/* Demo users */}
                {/* <div className="rounded-xl border border-blue-100 bg-blue-50/50 px-4 py-4 text-center">

                  <p className="text-sm font-semibold text-[#09265A]">
                    Demo users — admin / reviewer / officer
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    See README for passwords
                  </p>

                </div> */}

              </form>

            </div>


            {/* Footer */}
            <div className="mt-7 text-center">

              <div className="flex items-center justify-center gap-2">

                <div className="relative h-6 w-6">
                  <div className="absolute left-0 top-1 h-5 w-5 rounded-full bg-blue-200" />
                  <div className="absolute left-2 top-1 h-5 w-5 rounded-full bg-blue-500" />
                </div>

                <p className="font-bold text-[#09265A]">
                  Legal<span className="text-blue-500">Vision</span>
                </p>

              </div>

              <p className="mt-2 text-xs text-slate-400">
                Legal Metrology (Packaged Commodities) Rules, 2011
              </p>

              <div className="mx-auto mt-4 h-1 w-10 rounded-full bg-blue-500" />

            </div>

          </div>
        </section>

      </div>
    </div>
  );
}