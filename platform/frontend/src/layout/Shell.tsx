import { NavLink, Navigate, Outlet, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../auth/AuthContext";

const NAV = [
  {
    to: "/",
    label: "Dashboard",
    icon: "▦",
    roles: ["admin", "reviewer", "officer"],
  },
  {
    to: "/scan",
    label: "Scan Product",
    icon: "⇪",
    roles: ["admin", "reviewer", "officer"],
  },
  {
    to: "/repository",
    label: "Repository",
    icon: "⌕",
    roles: ["admin", "reviewer", "officer"],
  },
  {
    to: "/products",
    label: "Products",
    icon: "▤",
    roles: ["admin", "reviewer", "officer"],
  },
  {
    to: "/rules",
    label: "LMPC Rules",
    icon: "§",
    roles: ["admin", "reviewer", "officer"],
  },
  {
    to: "/users",
    label: "Users",
    icon: "☺",
    roles: ["admin"],
  },
];

export default function Shell() {
  const { user, ready, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-100 border-t-blue-700" />
          <p className="text-sm text-slate-500">Loading…</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const items = NAV.filter((n) => n.roles.includes(user.role));

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-slate-50">

      {/* =====================================================
          MOBILE TOP BAR
      ====================================================== */}
      <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 shadow-sm lg:hidden">

        {/* Logo */}
        <div className="flex items-center gap-3">

          <div className="relative h-9 w-9 shrink-0">
            <div className="absolute left-0 top-1 h-7 w-7 rounded-full bg-blue-200" />
            <div className="absolute left-2.5 top-1 h-7 w-7 rounded-full bg-blue-600" />
          </div>

          <div>
            <p className="text-lg font-bold leading-none text-[#09265A]">
              Legal<span className="text-blue-600">Vision</span>
            </p>

            <p className="mt-1 text-[9px] uppercase tracking-wider text-slate-400">
              Compliance Platform
            </p>
          </div>

        </div>

        {/* Menu Button */}
        <button
          type="button"
          onClick={() => setMobileOpen((prev) => !prev)}
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-[#09265A] transition hover:bg-blue-50"
          aria-label="Toggle navigation"
        >
          {mobileOpen ? (
            <svg
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path
                strokeLinecap="round"
                d="M6 6l12 12M18 6L6 18"
              />
            </svg>
          ) : (
            <svg
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path
                strokeLinecap="round"
                d="M4 7h16M4 12h16M4 17h16"
              />
            </svg>
          )}
        </button>

      </header>


      {/* =====================================================
          MOBILE SIDEBAR
      ====================================================== */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">

          {/* Overlay */}
          <div
            className="absolute inset-0 bg-[#061B41]/50 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />

          {/* Sidebar */}
          <aside className="absolute left-0 top-0 flex h-full w-[280px] flex-col bg-[#061B41] text-white shadow-2xl">

            {/* Mobile sidebar header */}
            <div className="border-b border-white/10 px-5 py-5">

              <div className="flex items-center justify-between">

                <div className="flex items-center gap-3">

                  <div className="relative h-9 w-9">
                    <div className="absolute left-0 top-1 h-7 w-7 rounded-full bg-blue-200" />
                    <div className="absolute left-2.5 top-1 h-7 w-7 rounded-full bg-blue-500" />
                  </div>

                  <div>
                    <p className="text-lg font-bold">
                      Legal<span className="text-blue-400">Vision</span>
                    </p>

                    <p className="text-[9px] uppercase tracking-wider text-blue-200/60">
                      Compliance Platform
                    </p>
                  </div>

                </div>

                <button
                  onClick={() => setMobileOpen(false)}
                  className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10 text-white hover:bg-white/15"
                  aria-label="Close navigation"
                >
                  <svg
                    className="h-5 w-5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path
                      strokeLinecap="round"
                      d="M6 6l12 12M18 6L6 18"
                    />
                  </svg>
                </button>

              </div>

              <p className="mt-4 text-xs leading-5 text-blue-200/60">
                Legal Metrology (Packaged Commodities) Rules, 2011
              </p>

            </div>


            {/* Navigation */}
            <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">

              <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-blue-300/50">
                Main Menu
              </p>

              {items.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  end={n.to === "/"}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `group flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition-all ${
                      isActive
                        ? "bg-blue-500 text-white shadow-lg shadow-blue-950/30"
                        : "text-blue-100/70 hover:bg-white/[0.08] hover:text-white"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span
                        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-base ${
                          isActive
                            ? "bg-white/15"
                            : "bg-white/[0.05]"
                        }`}
                      >
                        {n.icon}
                      </span>

                      <span className="font-medium">
                        {n.label}
                      </span>

                      {isActive && (
                        <svg
                          className="ml-auto h-4 w-4"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M9 18l6-6-6-6"
                          />
                        </svg>
                      )}
                    </>
                  )}
                </NavLink>
              ))}

            </nav>


            {/* Mobile User */}
            <div className="border-t border-white/10 p-4">

              <div className="rounded-2xl bg-white/[0.06] p-3">

                <div className="flex items-center gap-3">

                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-blue-700 text-sm font-bold">
                    {user.full_name?.charAt(0)?.toUpperCase()}
                  </div>

                  <div className="min-w-0">

                    <p className="truncate text-sm font-semibold">
                      {user.full_name}
                    </p>

                    <p className="mt-0.5 text-xs capitalize text-blue-300">
                      {user.role}
                    </p>

                  </div>

                </div>

                <button
                  className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 px-3 py-2.5 text-xs font-medium text-blue-200 transition hover:bg-white/10 hover:text-white"
                  onClick={handleLogout}
                >
                  <svg
                    className="h-4 w-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M10 17l5-5-5-5"
                    />

                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M15 12H3"
                    />

                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M21 19V5a2 2 0 00-2-2h-6"
                    />
                  </svg>

                  Sign out
                </button>

              </div>

            </div>

          </aside>

        </div>
      )}


      {/* =====================================================
          MAIN APPLICATION
          
          IMPORTANT:
          This is NOT hidden on mobile.
      ====================================================== */}
      <div className="flex min-h-[calc(100vh-4rem)]">

        {/* =====================================================
            DESKTOP SIDEBAR
        ====================================================== */}
        <aside className="hidden w-64 shrink-0 flex-col bg-[#061B41] text-white lg:flex">

          {/* Logo */}
          <div className="border-b border-white/10 px-5 py-6">

            <div className="flex items-center gap-3">

              <div className="relative h-10 w-10 shrink-0">
                <div className="absolute left-0 top-1 h-8 w-8 rounded-full bg-blue-200" />
                <div className="absolute left-3 top-1 h-8 w-8 rounded-full bg-blue-500" />
              </div>

              <div>
                <p className="text-xl font-bold tracking-tight">
                  Legal<span className="text-blue-400">Vision</span>
                </p>

                <p className="mt-1 text-[9px] uppercase tracking-[0.2em] text-blue-200/60">
                  Compliance Platform
                </p>
              </div>

            </div>

            <div className="mt-5 h-px bg-gradient-to-r from-blue-400/50 to-transparent" />

            <p className="mt-4 text-xs leading-5 text-blue-200/60">
              Legal Metrology (Packaged Commodities) Rules, 2011
            </p>

          </div>


          {/* Desktop Navigation */}
          <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">

            <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-blue-300/50">
              Main Menu
            </p>

            {items.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/"}
                className={({ isActive }) =>
                  `group relative flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition-all duration-200 ${
                    isActive
                      ? "bg-blue-500 text-white shadow-lg shadow-blue-950/30"
                      : "text-blue-100/65 hover:bg-white/[0.07] hover:text-white"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <span className="absolute left-0 h-7 w-1 rounded-r-full bg-white" />
                    )}

                    <span
                      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-base ${
                        isActive
                          ? "bg-white/15"
                          : "bg-white/[0.05] group-hover:bg-blue-500/20"
                      }`}
                    >
                      {n.icon}
                    </span>

                    <span className="font-medium">
                      {n.label}
                    </span>

                    {isActive && (
                      <svg
                        className="ml-auto h-4 w-4"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M9 18l6-6-6-6"
                        />
                      </svg>
                    )}
                  </>
                )}
              </NavLink>
            ))}

          </nav>


          {/* Desktop User */}
          <div className="border-t border-white/10 p-4">

            <div className="rounded-2xl bg-white/[0.06] p-3">

              <div className="flex items-center gap-3">

                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-blue-700 text-sm font-bold shadow-lg">
                  {user.full_name?.charAt(0)?.toUpperCase()}
                </div>

                <div className="min-w-0">

                  <p className="truncate text-sm font-semibold text-white">
                    {user.full_name}
                  </p>

                  <div className="mt-0.5 flex items-center gap-1.5">

                    <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />

                    <p className="text-xs capitalize text-blue-300">
                      {user.role}
                    </p>

                  </div>

                </div>

              </div>

              <button
                className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-blue-200 transition hover:bg-white/10 hover:text-white"
                onClick={handleLogout}
              >
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M10 17l5-5-5-5"
                  />

                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M15 12H3"
                  />

                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21 19V5a2 2 0 00-2-2h-6"
                  />
                </svg>

                Sign out
              </button>

            </div>

          </div>

        </aside>


        {/* =====================================================
            MAIN CONTENT
        ====================================================== */}
        <div className="flex min-w-0 flex-1 flex-col">

          {/* Desktop Header */}
          <header className="sticky top-0 z-20 hidden min-h-[72px] items-center justify-between border-b border-slate-200 bg-white/95 px-6 backdrop-blur-md sm:flex xl:px-8">

            <div className="min-w-0">

              <p className="text-sm font-medium text-slate-500">
                Enforcement Monitoring
              </p>

              <p className="mt-0.5 text-sm font-semibold text-[#09265A]">
                Legal Metrology Department
              </p>

            </div>


            {/* System Status */}
            <div className="flex items-center gap-3">

              <div className="flex h-9 items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-4">

                <span className="relative flex h-2.5 w-2.5">

                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-60" />

                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-blue-500" />

                </span>

                <span className="text-xs font-medium text-[#0B3B82]">
                  System Online
                </span>

              </div>

            </div>

          </header>


          {/* Mobile Status Bar */}
          <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 sm:hidden">

            <div>
              <p className="text-xs font-medium text-slate-500">
                Enforcement Monitoring
              </p>

              <p className="mt-0.5 text-xs font-semibold text-[#09265A]">
                Legal Metrology Department
              </p>
            </div>

            <div className="flex items-center gap-1.5">

              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500" />
              </span>

              <span className="text-[10px] font-medium text-blue-700">
                Online
              </span>

            </div>

          </div>


          {/* =====================================================
              PAGE CONTENT

              Outlet is now visible on ALL screen sizes.
          ====================================================== */}
          <main className="min-w-0 flex-1 overflow-x-hidden bg-slate-50 p-4 sm:p-6 xl:p-8">

            <Outlet />

          </main>

        </div>

      </div>

    </div>
  );
}