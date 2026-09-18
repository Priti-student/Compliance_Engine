import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import Pagination from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import type { InspectionSummary, Page } from "../types";

export default function RepositoryPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page<InspectionSummary> | null>(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setBusy(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        size: "12",
      });

      if (q.trim()) params.set("q", q.trim());
      if (status) params.set("compliance_status", status);
      if (category) params.set("category", category);

      setData(
        await api<Page<InspectionSummary>>(
          `/search?${params.toString()}`
        )
      );
    } catch {
      setData(null);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const submit = (e?: React.FormEvent) => {
    e?.preventDefault();
    setPage(1);
    void load();
  };

  return (
    <div className="w-full space-y-6">
      {/* Page Header */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">
          Inspection Repository
        </p>

        <div className="mt-1 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#09265A] sm:text-3xl">
              Product Repository
            </h1>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Search and review previously scanned packaged commodities and
              their compliance results.
            </p>
          </div>

          {data && (
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-medium text-[#0B3B82]">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-600" />
              {data.total} inspection{data.total !== 1 ? "s" : ""}
            </div>
          )}
        </div>
      </div>

      {/* Search / Filter Card */}
      <form
        className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5"
        onSubmit={submit}
      >
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
            <svg
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <circle cx="11" cy="11" r="6.5" />
              <path
                strokeLinecap="round"
                d="M16 16l4.5 4.5"
              />
            </svg>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-[#09265A]">
              Search & Filter
            </h2>
            <p className="text-xs text-slate-400">
              Find inspections by product, category or compliance status
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-[minmax(0,1fr)_180px_180px_auto]">
          {/* Search */}
          <div className="relative">
            <svg
              className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <circle cx="11" cy="11" r="6.5" />
              <path
                strokeLinecap="round"
                d="M16 16l4.5 4.5"
              />
            </svg>

            <input
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-3.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
              placeholder="Search product, brand, manufacturer, token…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>

          {/* Status */}
          <select
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">All statuses</option>
            <option value="compliant">Compliant</option>
            <option value="non_compliant">Non-compliant</option>
            <option value="needs_review">Needs review</option>
            <option value="not_applicable">Not applicable</option>
          </select>

          {/* Category */}
          <input
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
            placeholder="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />

          {/* Search Button */}
          <button
            className="flex items-center justify-center gap-2 rounded-xl bg-[#0B3B82] px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-900/10 transition hover:bg-[#092F6B] disabled:cursor-not-allowed disabled:opacity-60"
            type="submit"
            disabled={busy}
          >
            {busy ? (
              <>
                <svg
                  className="h-4 w-4 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="9"
                    stroke="currentColor"
                    strokeWidth="3"
                    className="opacity-25"
                  />
                  <path
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z"
                  />
                </svg>
                Searching
              </>
            ) : (
              <>
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <circle cx="11" cy="11" r="6.5" />
                  <path
                    strokeLinecap="round"
                    d="M16 16l4.5 4.5"
                  />
                </svg>
                Search
              </>
            )}
          </button>
        </div>
      </form>

      {/* Repository Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {/* Table Header */}
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 sm:px-6">
          <div>
            <h2 className="text-sm font-semibold text-[#09265A]">
              Inspection Records
            </h2>
            <p className="mt-0.5 text-xs text-slate-400">
              Previously scanned products
            </p>
          </div>

          {busy && (
            <div className="flex items-center gap-2 text-xs text-blue-600">
              <span className="h-2 w-2 animate-pulse rounded-full bg-blue-600" />
              Loading
            </div>
          )}
        </div>

        {/* Responsive Table */}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px]">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/70">
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Product
                </th>

                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Category
                </th>

                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Compliance
                </th>

                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Stats
                </th>

                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Officer
                </th>

                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Date
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {(data?.items || []).map((r) => (
                <tr
                  key={r.token}
                  className="group transition hover:bg-blue-50/30"
                >
                  {/* Product */}
                  <td className="px-5 py-4">
                    <Link
                      to={`/inspections/${r.token}`}
                      className="font-semibold text-[#0B3B82] transition hover:text-blue-600 hover:underline"
                    >
                      {r.product?.generic_name || "Unnamed"}
                    </Link>

                    <div className="mt-1 font-mono text-[10px] text-slate-400">
                      {r.token}
                    </div>
                  </td>

                  {/* Category */}
                  <td className="px-5 py-4 text-sm text-slate-600">
                    {r.product?.category || "—"}
                  </td>

                  {/* Compliance */}
                  <td className="px-5 py-4">
                    <StatusBadge status={r.compliance_status} />
                  </td>

                  {/* Stats */}
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="rounded-md border border-amber-100 bg-amber-50 px-2 py-1 font-medium text-amber-700">
                        {r.stats?.missing ?? 0} missing
                      </span>

                      <span className="rounded-md border border-red-100 bg-red-50 px-2 py-1 font-medium text-red-600">
                        {r.stats?.non_compliant ?? 0} non
                      </span>
                    </div>
                  </td>

                  {/* Officer */}
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-[10px] font-bold text-blue-700">
                        {(
                          r.officer?.full_name ||
                          r.officer?.username ||
                          "?"
                        )
                          .charAt(0)
                          .toUpperCase()}
                      </div>

                      <span className="max-w-[150px] truncate text-xs text-slate-600">
                        {r.officer?.full_name ||
                          r.officer?.username ||
                          "—"}
                      </span>
                    </div>
                  </td>

                  {/* Date */}
                  <td className="px-5 py-4 text-xs text-slate-500">
                    {new Date(
                      r.created_at || ""
                    ).toLocaleDateString()}
                  </td>
                </tr>
              ))}

              {!busy && !data?.items?.length && (
                <tr>
                  <td
                    className="px-5 py-14 text-center"
                    colSpan={6}
                  >
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                      <svg
                        className="h-6 w-6"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.7"
                      >
                        <circle cx="11" cy="11" r="6.5" />
                        <path
                          strokeLinecap="round"
                          d="M16 16l4.5 4.5"
                        />
                      </svg>
                    </div>

                    <p className="mt-3 text-sm font-medium text-slate-600">
                      No inspections found
                    </p>

                    <p className="mt-1 text-xs text-slate-400">
                      No inspections match your current search.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile hint */}
        <div className="border-t border-slate-100 bg-slate-50 px-5 py-2.5 text-center text-[10px] text-slate-400 sm:hidden">
          ← Swipe horizontally to view all columns →
        </div>
      </div>

      {/* Pagination */}
      {data && (
        <div className="flex justify-center sm:justify-end">
          <Pagination
            page={page}
            size={12}
            total={data.total}
            onChange={setPage}
          />
        </div>
      )}
    </div>
  );
}