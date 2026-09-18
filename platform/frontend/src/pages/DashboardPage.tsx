import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import StatCard from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import type { DashboardSummary, InspectionSummary } from "../types";

const PIE_COLORS: Record<string, string> = {
  compliant: "#2563EB",
  non_compliant: "#DC2626",
  needs_review: "#F59E0B",
  not_applicable: "#64748B",
};

function useFetch<T>(path: string, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;

    api<T>(path)
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e.message));

    return () => {
      alive = false;
    };

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error };
}

export default function DashboardPage() {
  const { data: summary } =
    useFetch<DashboardSummary>("/dashboard/summary");

  const { data: trend } =
    useFetch<
      {
        date: string;
        violations: number;
        missing: number;
        non_compliant: number;
      }[]
    >("/dashboard/violation-trend?days=30");

  const { data: statuses } =
    useFetch<{ status: string; count: number }[]>(
      "/dashboard/status-distribution"
    );

  const { data: topViolations } =
    useFetch<
      {
        rule_id: string;
        rule_reference: string;
        count: number;
      }[]
    >("/dashboard/top-violations?limit=8");

  const { data: officers } =
    useFetch<
      {
        officer: string;
        scans: number;
        violations: number;
      }[]
    >("/dashboard/officer-activity");

  const { data: recent } =
    useFetch<InspectionSummary[]>(
      "/dashboard/recent?limit=8"
    );

  const s = summary;

  const pieData = (statuses || []).map((d) => ({
    ...d,
    fill: PIE_COLORS[d.status] || "#94a3b8",
  }));

  return (
    <div className="w-full min-w-0 space-y-5 sm:space-y-6">

      {/* =====================================================
          PAGE HEADER
      ====================================================== */}

      <div className="flex min-w-0 flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

        <div className="min-w-0">
          <div className="mb-1 flex items-center gap-2">
            <span className="h-2 w-2 shrink-0 rounded-full bg-blue-600" />

            <p className="truncate text-xs font-semibold uppercase tracking-[0.15em] text-blue-600">
              Enforcement Monitoring
            </p>
          </div>

          <h1 className="text-xl font-bold tracking-tight text-[#09265A] sm:text-2xl lg:text-3xl">
            Enforcement Dashboard
          </h1>

          <p className="mt-1 text-xs text-slate-500 sm:text-sm">
            Monitor product inspections, compliance and violations.
          </p>
        </div>

        <Link
          to="/scan"
          className="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-xl bg-[#0B3B82] px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-900/20 transition hover:bg-blue-700 sm:w-auto"
        >
          <span className="text-lg leading-none">+</span>
          New Scan

          <svg
            className="h-4 w-4"
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
        </Link>

      </div>


      {/* =====================================================
          STAT CARDS
      ====================================================== */}

      <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">

        <div className="min-w-0 overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">
          <StatCard
            label="Total inspections"
            value={s?.total_inspections ?? "–"}
            sub={`${s?.total_products ?? 0} products in repository`}
          />
        </div>

        <div className="min-w-0 overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">
          <StatCard
            label="Compliance rate"
            value={s ? `${s.compliance_rate_pct}%` : "–"}
            sub="of all scans"
            tone="ok"
          />
        </div>

        <div className="min-w-0 overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">
          <StatCard
            label="Violations found"
            value={s?.total_violations ?? "–"}
            sub={`${s?.total_missing_declarations ?? 0} missing declarations`}
            tone="bad"
          />
        </div>

        <div className="min-w-0 overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">
          <StatCard
            label="Active officers"
            value={s?.active_officers ?? "–"}
            sub={`${s?.reviewed_count ?? 0} inspections reviewed`}
            tone="warn"
          />
        </div>

      </div>


      {/* =====================================================
          VIOLATION TREND + COMPLIANCE
      ====================================================== */}

      <div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-3">

        {/* Violation Trend */}
        <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5 xl:col-span-2">

          <div className="mb-4 flex min-w-0 flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">

            <div className="min-w-0">
              <h2 className="truncate font-semibold text-[#09265A]">
                Violation Trend
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                Inspection activity over the last 30 days
              </p>
            </div>

            <span className="w-fit shrink-0 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
              Last 30 days
            </span>

          </div>

          {/* Chart wrapper */}
          <div className="w-full min-w-0">

            <ResponsiveContainer
              width="100%"
              height={260}
              minWidth={0}
            >
              <LineChart
                data={trend || []}
                margin={{
                  top: 5,
                  right: 5,
                  left: -15,
                  bottom: 5,
                }}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#E2E8F0"
                  vertical={false}
                />

                <XAxis
                  dataKey="date"
                  fontSize={10}
                  stroke="#94A3B8"
                  tickLine={false}
                  axisLine={false}
                  minTickGap={20}
                />

                <YAxis
                  fontSize={10}
                  stroke="#94A3B8"
                  allowDecimals={false}
                  tickLine={false}
                  axisLine={false}
                  width={35}
                />

                <Tooltip
                  contentStyle={{
                    borderRadius: "12px",
                    border: "1px solid #DBEAFE",
                    boxShadow:
                      "0 10px 30px rgba(9,38,90,0.10)",
                    backgroundColor: "#ffffff",
                    fontSize: "12px",
                  }}
                />

                <Legend
                  wrapperStyle={{
                    fontSize: "11px",
                  }}
                />

                <Line
                  type="monotone"
                  dataKey="violations"
                  stroke="#2563EB"
                  strokeWidth={3}
                  dot={false}
                  activeDot={{ r: 5 }}
                  name="Violations"
                />

                <Line
                  type="monotone"
                  dataKey="missing"
                  stroke="#60A5FA"
                  strokeWidth={2}
                  dot={false}
                  name="Missing"
                />

              </LineChart>
            </ResponsiveContainer>

          </div>

        </section>


        {/* Compliance Status */}
        <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">

          <div className="mb-2">
            <h2 className="font-semibold text-[#09265A]">
              Compliance Status
            </h2>

            <p className="mt-1 text-xs text-slate-400">
              Distribution of inspection results
            </p>
          </div>

          <div className="w-full min-w-0">

            <ResponsiveContainer
              width="100%"
              height={250}
              minWidth={0}
            >
              <PieChart>

                <Pie
                  data={pieData}
                  dataKey="count"
                  nameKey="status"
                  innerRadius="45%"
                  outerRadius="68%"
                  paddingAngle={3}
                  label
                >
                  {pieData.map((d, i) => (
                    <Cell
                      key={i}
                      fill={d.fill}
                      stroke="#ffffff"
                      strokeWidth={3}
                    />
                  ))}
                </Pie>

                <Tooltip
                  contentStyle={{
                    borderRadius: "12px",
                    border: "1px solid #DBEAFE",
                    boxShadow:
                      "0 10px 30px rgba(9,38,90,0.10)",
                    fontSize: "12px",
                  }}
                />

              </PieChart>
            </ResponsiveContainer>

          </div>

          {/* Status legend */}
          <div className="grid grid-cols-2 gap-x-3 gap-y-2">

            {pieData.map((item) => (
              <div
                key={item.status}
                className="flex min-w-0 items-center gap-2"
              >
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: item.fill }}
                />

                <span className="truncate text-xs capitalize text-slate-500">
                  {item.status.replace("_", " ")}
                </span>
              </div>
            ))}

          </div>

        </section>

      </div>


      {/* =====================================================
          LOWER SECTION
      ====================================================== */}

      <div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-3">

        {/* Top Violated Rules */}
        <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">

          <div className="mb-4">
            <h2 className="font-semibold text-[#09265A]">
              Top Violated Rules
            </h2>

            <p className="mt-1 text-xs text-slate-400">
              Rules with the highest number of violations
            </p>
          </div>

          <div className="w-full min-w-0">

            <ResponsiveContainer
              width="100%"
              height={240}
              minWidth={0}
            >
              <BarChart
                data={(topViolations || []).map((v) => ({
                  rule: v.rule_id,
                  count: v.count,
                }))}
                layout="vertical"
                margin={{
                  left: 0,
                  right: 10,
                  top: 5,
                  bottom: 5,
                }}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#E2E8F0"
                  horizontal={false}
                />

                <XAxis
                  type="number"
                  fontSize={10}
                  allowDecimals={false}
                  stroke="#94A3B8"
                  tickLine={false}
                  axisLine={false}
                />

                <YAxis
                  type="category"
                  dataKey="rule"
                  width={55}
                  fontSize={9}
                  stroke="#64748B"
                  tickLine={false}
                  axisLine={false}
                />

                <Tooltip
                  contentStyle={{
                    borderRadius: "12px",
                    border: "1px solid #DBEAFE",
                    boxShadow:
                      "0 10px 30px rgba(9,38,90,0.10)",
                    fontSize: "12px",
                  }}
                />

                <Bar
                  dataKey="count"
                  fill="#2563EB"
                  radius={[0, 6, 6, 0]}
                />

              </BarChart>
            </ResponsiveContainer>

          </div>

        </section>


        {/* Officer Activity */}
        <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">

          <div className="mb-4">
            <h2 className="font-semibold text-[#09265A]">
              Officer Activity
            </h2>

            <p className="mt-1 text-xs text-slate-400">
              Scans and violations by officer
            </p>
          </div>

          <div className="w-full min-w-0">

            <ResponsiveContainer
              width="100%"
              height={240}
              minWidth={0}
            >
              <BarChart
                data={officers || []}
                margin={{
                  left: -15,
                  right: 5,
                  top: 5,
                  bottom: 5,
                }}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#E2E8F0"
                  vertical={false}
                />

                <XAxis
                  dataKey="officer"
                  fontSize={9}
                  stroke="#64748B"
                  tickLine={false}
                  axisLine={false}
                  interval={0}
                  tickFormatter={(value) =>
                    String(value).length > 8
                      ? `${String(value).slice(0, 8)}…`
                      : value
                  }
                />

                <YAxis
                  fontSize={10}
                  allowDecimals={false}
                  stroke="#64748B"
                  tickLine={false}
                  axisLine={false}
                  width={35}
                />

                <Tooltip
                  contentStyle={{
                    borderRadius: "12px",
                    border: "1px solid #DBEAFE",
                    boxShadow:
                      "0 10px 30px rgba(9,38,90,0.10)",
                    fontSize: "12px",
                  }}
                />

                <Legend
                  wrapperStyle={{
                    fontSize: "11px",
                  }}
                />

                <Bar
                  dataKey="scans"
                  fill="#0B3B82"
                  radius={[5, 5, 0, 0]}
                  name="Scans"
                />

                <Bar
                  dataKey="violations"
                  fill="#60A5FA"
                  radius={[5, 5, 0, 0]}
                  name="Violations"
                />

              </BarChart>
            </ResponsiveContainer>

          </div>

        </section>


        {/* Recent Inspections */}
        <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">

          <div className="mb-4 flex items-center justify-between gap-3">

            <div className="min-w-0">
              <h2 className="truncate font-semibold text-[#09265A]">
                Recent Inspections
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                Latest compliance activity
              </p>
            </div>

            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              ↗
            </span>

          </div>


          <ul className="divide-y divide-slate-100">

            {(recent || []).map((r) => (
              <li
                key={r.token}
                className="min-w-0 py-3 first:pt-1"
              >

                <Link
                  to={`/inspections/${r.token}`}
                  className="group block min-w-0"
                >

                  <div className="flex min-w-0 items-center gap-2">

                    <p className="min-w-0 flex-1 truncate text-sm font-semibold text-[#09265A] transition group-hover:text-blue-600">
                      {r.product?.generic_name ||
                        "Unnamed product"}
                    </p>

                    <svg
                      className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-1 group-hover:text-blue-500"
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

                  </div>

                  <div className="mt-1.5 flex flex-wrap items-center gap-2">

                    <StatusBadge
                      status={r.compliance_status}
                    />

                    <span className="text-xs text-slate-400">
                      {new Date(
                        r.created_at || ""
                      ).toLocaleDateString()}
                    </span>

                  </div>

                </Link>

              </li>
            ))}

            {!recent?.length && (
              <li className="py-8 text-center">

                <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 text-blue-400">
                  —
                </div>

                <p className="text-sm text-slate-400">
                  No inspections yet
                </p>

              </li>
            )}

          </ul>

        </section>

      </div>

    </div>
  );
}