import { ChangeEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, downloadFile, mediaUrl } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { SeverityBadge, StatusBadge } from "../components/StatusBadge";
import type { InspectionDetail } from "../types";

const VERDICT_STYLES: Record<string, string> = {
  compliant:
    "bg-emerald-50 text-emerald-800 border-emerald-200",
  non_compliant:
    "bg-red-50 text-red-800 border-red-200",
  needs_review:
    "bg-amber-50 text-amber-800 border-amber-200",
  not_applicable:
    "bg-slate-100 text-slate-700 border-slate-200",
};

export default function ReportPage() {
  const { token } = useParams();
  const { user } = useAuth();
  const [detail, setDetail] = useState<InspectionDetail | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    if (!token) return;

    try {
      setDetail(await api<InspectionDetail>(`/inspections/${token}`));
      setError("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load inspection"
      );
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (error) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-100">
            <svg
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <circle cx="12" cy="12" r="9" />
              <path
                strokeLinecap="round"
                d="M12 8v5M12 16h.01"
              />
            </svg>
          </div>
          <p className="pt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 animate-spin rounded-full border-4 border-blue-100 border-t-blue-700" />
          <p className="text-sm text-slate-500">
            Loading report…
          </p>
        </div>
      </div>
    );
  }

  const isReviewer =
    user?.role === "reviewer" || user?.role === "admin";

  const setWorkflow = async (status: string) => {
    setBusy(true);

    try {
      await api(`/inspections/${detail.token}`, {
        method: "PATCH",
        body: { workflow_status: status },
      });

      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Update failed"
      );
    } finally {
      setBusy(false);
    }
  };

  const uploadEvidence = async (
    e: ChangeEvent<HTMLInputElement>
  ) => {
    const files = e.target.files;

    if (!files?.length) return;

    setBusy(true);

    try {
      const form = new FormData();

      Array.from(files).forEach((f) =>
        form.append("files", f)
      );

      await api(`/inspections/${detail.token}/evidence`, {
        method: "POST",
        body: form,
      });

      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Upload failed"
      );
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  };

  const p = detail.product;
  const s = detail.stats || {};

  const zones =
    (
      detail.compliance_json?.scan as {
        zones?: {
          zone_type: string;
          bbox: number[];
        }[];
      }
    )?.zones || [];

  const downloadOrGenerate = async (
    t: "pdf" | "xlsx" | "json"
  ) => {
    const exists = detail.reports.some(
      (r) => r.report_type === t
    );

    if (!exists) {
      setBusy(true);

      try {
        await api(`/reports/${detail.token}`, {
          method: "POST",
          body: { report_type: t },
        });

        await load();
      } finally {
        setBusy(false);
      }
    }

    await downloadFile(
      `/reports/${detail.token}/${t}`,
      `${detail.token}.${t === "xlsx" ? "xlsx" : t}`
    );
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">
            Compliance Inspection Report
          </p>

          <h1 className="mt-1 break-words text-2xl font-bold tracking-tight text-[#09265A] sm:text-3xl">
            {p?.generic_name || "Inspection"}
          </h1>

          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className="rounded-lg bg-slate-100 px-2.5 py-1 font-mono text-[10px] text-slate-500">
              {detail.token}
            </span>

            <StatusBadge status={detail.compliance_status} />
            <StatusBadge status={detail.workflow_status} />

            <span className="text-xs text-slate-400">
              {new Date(
                detail.created_at || ""
              ).toLocaleString()}
            </span>
          </div>
        </div>

        {/* Download Buttons */}
        <div className="flex w-full flex-wrap gap-2 xl:w-auto">
          {(["pdf", "xlsx", "json"] as const).map((t) => (
            <button
              key={t}
              className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-blue-200 bg-white px-4 py-2.5 text-xs font-semibold text-[#0B3B82] shadow-sm transition hover:border-blue-300 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-60 sm:flex-none"
              disabled={busy}
              onClick={() => void downloadOrGenerate(t)}
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
                  d="M12 3v12"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M7.5 10.5L12 15l4.5-4.5"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 20h14"
                />
              </svg>
              Download {t.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Verdict */}
      <div
        className={`relative overflow-hidden rounded-2xl border p-5 shadow-sm sm:p-6 ${
          VERDICT_STYLES[detail.compliance_status] ||
          "bg-slate-100 text-slate-700 border-slate-200"
        }`}
      >
        <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-white/40" />
        <div className="absolute -bottom-12 -left-8 h-28 w-28 rounded-full bg-white/30" />

        <div className="relative">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/70">
              {detail.compliance_status === "compliant" ? (
                <svg
                  className="h-6 w-6"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 12l4 4L19 6"
                  />
                </svg>
              ) : (
                <svg
                  className="h-6 w-6"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <circle cx="12" cy="12" r="9" />
                  <path
                    strokeLinecap="round"
                    d="M12 8v5M12 16h.01"
                  />
                </svg>
              )}
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider opacity-70">
                Compliance Verdict
              </p>

              <p className="mt-0.5 text-xl font-extrabold uppercase tracking-wide sm:text-2xl">
                {detail.compliance_status.replace(
                  /_/g,
                  " "
                )}
              </p>
            </div>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-5">
            <div className="rounded-xl bg-white/50 p-3">
              <p className="text-[10px] uppercase tracking-wider opacity-60">
                Total checks
              </p>
              <p className="mt-1 text-lg font-bold">
                {s.total_checks || 0}
              </p>
            </div>

            <div className="rounded-xl bg-white/50 p-3">
              <p className="text-[10px] uppercase tracking-wider opacity-60">
                Compliant
              </p>
              <p className="mt-1 text-lg font-bold">
                {s.compliant || 0}
              </p>
            </div>

            <div className="rounded-xl bg-white/50 p-3">
              <p className="text-[10px] uppercase tracking-wider opacity-60">
                Non-compliant
              </p>
              <p className="mt-1 text-lg font-bold">
                {s.non_compliant || 0}
              </p>
            </div>

            <div className="rounded-xl bg-white/50 p-3">
              <p className="text-[10px] uppercase tracking-wider opacity-60">
                Missing
              </p>
              <p className="mt-1 text-lg font-bold">
                {s.missing || 0}
              </p>
            </div>

            <div className="rounded-xl bg-white/50 p-3">
              <p className="text-[10px] uppercase tracking-wider opacity-60">
                Review
              </p>
              <p className="mt-1 text-lg font-bold">
                {s.needs_review || 0}
              </p>
            </div>
          </div>

          {detail.advice?.length ? (
            <div className="mt-5 rounded-xl bg-white/50 p-4">
              <p className="text-xs font-bold uppercase tracking-wider opacity-70">
                Recommendations
              </p>

              <ul className="mt-2 space-y-1.5 text-xs">
                {detail.advice.map((a) => (
                  <li
                    key={a}
                    className="flex items-start gap-2"
                  >
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-current" />
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      </div>

      {/* Product + Image */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        {/* Product & Inspection */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                <svg
                  className="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 5h14v14H5z"
                  />
                  <path
                    strokeLinecap="round"
                    d="M8 9h8M8 13h8M8 17h4"
                  />
                </svg>
              </div>

              <div>
                <h2 className="text-sm font-semibold text-[#09265A]">
                  Product & Inspection
                </h2>
                <p className="text-xs text-slate-400">
                  Inspection information
                </p>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-slate-100">
                {p ? (
                  <>
                    <tr>
                      <td className="w-1/3 px-5 py-3 font-medium text-slate-500">
                        Product
                      </td>
                      <td className="px-5 py-3 font-semibold text-[#09265A]">
                        {p.generic_name}
                      </td>
                    </tr>

                    <tr>
                      <td className="px-5 py-3 font-medium text-slate-500">
                        Brand / category
                      </td>
                      <td className="px-5 py-3 text-slate-700">
                        {`${p.brand || "-"} / ${
                          p.category || "-"
                        }`}
                      </td>
                    </tr>

                    <tr>
                      <td className="px-5 py-3 font-medium text-slate-500">
                        Net qty / MRP
                      </td>
                      <td className="px-5 py-3 text-slate-700">
                        {`${p.net_quantity_text || "-"} / ${
                          p.mrp || "-"
                        }`}
                      </td>
                    </tr>

                    <tr>
                      <td className="px-5 py-3 font-medium text-slate-500">
                        Manufacturer
                      </td>
                      <td className="px-5 py-3 text-slate-700">
                        {p.manufacturer || "-"}
                      </td>
                    </tr>
                  </>
                ) : null}

                <tr>
                  <td className="px-5 py-3 font-medium text-slate-500">
                    Inspecting officer
                  </td>
                  <td className="px-5 py-3 text-slate-700">
                    {detail.officer?.full_name || "-"}
                  </td>
                </tr>

                <tr>
                  <td className="px-5 py-3 font-medium text-slate-500">
                    Reviewed by
                  </td>
                  <td className="px-5 py-3 text-slate-700">
                    {detail.reviewer?.full_name || "—"}
                  </td>
                </tr>

                <tr>
                  <td className="px-5 py-3 font-medium text-slate-500">
                    Image
                  </td>
                  <td className="px-5 py-3 text-xs text-slate-600">
                    {detail.image_name}
                  </td>
                </tr>

                <tr>
                  <td className="px-5 py-3 font-medium text-slate-500">
                    Remarks
                  </td>
                  <td className="px-5 py-3 text-slate-700">
                    {detail.remarks || "—"}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Package Image */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                <svg
                  className="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <rect
                    x="3"
                    y="3"
                    width="18"
                    height="18"
                    rx="2"
                  />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21 15l-5-5L5 21"
                  />
                </svg>
              </div>

              <div>
                <h2 className="text-sm font-semibold text-[#09265A]">
                  Package Image
                </h2>
                <p className="text-xs text-slate-400">
                  Detected declaration zones
                </p>
              </div>
            </div>
          </div>

          <div className="p-5">
            {detail.image_name ? (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <img
                  src={mediaUrl(
                    `/inspections/${detail.token}/image?annotated=true`
                  )}
                  alt="Annotated package"
                  className="mx-auto max-h-96 w-full rounded-lg object-contain"
                />
              </div>
            ) : (
              <div className="flex min-h-[250px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50">
                <p className="text-xs text-slate-400">
                  No image stored for this inspection.
                </p>
              </div>
            )}

            <div className="mt-3 rounded-lg bg-blue-50 px-3 py-2.5 text-xs text-blue-800">
              <span className="font-semibold">
                {zones.length}
              </span>{" "}
              declaration zone(s) detected
              {zones.length > 0 && (
                <>
                  :{" "}
                  <span className="font-medium">
                    {zones
                      .map((z) => z.zone_type)
                      .join(", ")}
                  </span>
                </>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* Extracted Declarations */}
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
              >
                <path
                  strokeLinecap="round"
                  d="M7 6h10M7 10h10M7 14h7"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 3h14v18H5z"
                />
              </svg>
            </div>

            <div>
              <h2 className="text-sm font-semibold text-[#09265A]">
                Extracted Declarations
              </h2>
              <p className="text-xs text-slate-400">
                Information extracted from the package label
              </p>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px]">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/70">
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Field
                </th>
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Value
                </th>
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Source zone
                </th>
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Confidence
                </th>
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Method
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {detail.declarations.map((d, i) => (
                <tr
                  key={i}
                  className="transition hover:bg-blue-50/30"
                >
                  <td className="px-5 py-3 font-mono text-xs font-medium text-[#0B3B82]">
                    {d.field_name}
                  </td>

                  <td className="px-5 py-3 text-sm text-slate-700">
                    {d.value || "—"}
                  </td>

                  <td className="px-5 py-3 text-xs text-slate-500">
                    {d.source_zone || "—"}
                  </td>

                  <td className="px-5 py-3">
                    <span className="rounded-md bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700">
                      {d.confidence.toFixed(2)}
                    </span>
                  </td>

                  <td className="px-5 py-3 text-xs text-slate-500">
                    {d.method || "—"}
                  </td>
                </tr>
              ))}

              {!detail.declarations.length && (
                <tr>
                  <td
                    className="px-5 py-8 text-center text-sm text-slate-400"
                    colSpan={5}
                  >
                    No declarations extracted.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Violations */}
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-50 text-amber-700">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 3l9 17H3L12 3z"
                />
                <path
                  strokeLinecap="round"
                  d="M12 9v5M12 17h.01"
                />
              </svg>
            </div>

            <div>
              <h2 className="text-sm font-semibold text-[#09265A]">
                Violations / Review Items
              </h2>
              <p className="text-xs text-slate-400">
                Compliance rules requiring attention
              </p>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[800px]">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/70">
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Rule
                </th>
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Reference
                </th>
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Status
                </th>
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Severity
                </th>
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Reason
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {detail.violations.map((v, i) => (
                <tr
                  key={i}
                  className="transition hover:bg-blue-50/30"
                >
                  <td className="px-5 py-3 font-mono text-xs font-medium text-[#0B3B82]">
                    {v.rule_id}
                  </td>

                  <td className="px-5 py-3 text-xs text-slate-500">
                    {v.rule_reference || "—"}
                  </td>

                  <td className="px-5 py-3">
                    <StatusBadge status={v.status} />
                  </td>

                  <td className="px-5 py-3">
                    <SeverityBadge severity={v.severity} />
                  </td>

                  <td className="px-5 py-3 text-xs leading-5 text-slate-600">
                    {v.reason}
                  </td>
                </tr>
              ))}

              {!detail.violations.length && (
                <tr>
                  <td
                    className="px-5 py-8 text-center text-sm text-slate-400"
                    colSpan={5}
                  >
                    No violations detected.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Font Metrics + Evidence */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        {/* Font Metrics */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                <svg
                  className="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <path
                    strokeLinecap="round"
                    d="M5 19L10 5M14 19l5-14M7 14h10"
                  />
                </svg>
              </div>

              <div>
                <h2 className="text-sm font-semibold text-[#09265A]">
                  Font Metrics / Readability
                </h2>
                <p className="text-xs text-slate-400">
                  Character size and contrast analysis
                </p>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px]">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/70">
                  <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Zone
                  </th>
                  <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Char px
                  </th>
                  <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Height mm
                  </th>
                  <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Contrast
                  </th>
                  <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Calibrated
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {detail.font_metrics.map((m, i) => (
                  <tr
                    key={i}
                    className="transition hover:bg-blue-50/30"
                  >
                    <td className="px-5 py-3 font-mono text-xs text-[#0B3B82]">
                      {m.zone_type}
                    </td>

                    <td className="px-5 py-3 text-sm text-slate-700">
                      {m.char_height_px_median.toFixed(1)}
                    </td>

                    <td className="px-5 py-3 text-sm text-slate-700">
                      {m.calibrated
                        ? m.char_height_mm_median.toFixed(3)
                        : "—"}
                    </td>

                    <td className="px-5 py-3 text-sm font-medium text-slate-700">
                      {m.contrast_ratio.toFixed(2)}
                    </td>

                    <td className="px-5 py-3">
                      <span
                        className={`rounded-md px-2 py-1 text-xs font-semibold ${
                          m.calibrated
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-slate-100 text-slate-500"
                        }`}
                      >
                        {m.calibrated ? "yes" : "no"}
                      </span>
                    </td>
                  </tr>
                ))}

                {!detail.font_metrics.length && (
                  <tr>
                    <td
                      className="px-5 py-8 text-center text-sm text-slate-400"
                      colSpan={5}
                    >
                      No font readings.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Supporting Evidence */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                <svg
                  className="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M15.5 6.5l-7.8 7.8a3 3 0 004.2 4.2l8-8a4.5 4.5 0 00-6.4-6.4l-8.1 8.1a6 6 0 008.5 8.5l7.2-7.2"
                  />
                </svg>
              </div>

              <div>
                <h2 className="text-sm font-semibold text-[#09265A]">
                  Supporting Evidence
                </h2>
                <p className="text-xs text-slate-400">
                  Photos and documents attached to this inspection
                </p>
              </div>
            </div>
          </div>

          <div className="p-5">
            <ul className="divide-y divide-slate-100">
              {detail.evidence.map((e) => (
                <li
                  key={e.id}
                  className="flex items-center justify-between gap-3 py-3"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
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
                          d="M5 5h14v14H5z"
                        />
                        <path
                          strokeLinecap="round"
                          d="M8 9h8M8 13h5"
                        />
                      </svg>
                    </div>

                    <span className="truncate text-sm text-slate-700">
                      {e.filename}
                    </span>
                  </div>

                  <button
                    className="shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold text-[#0B3B82] transition hover:bg-blue-50"
                    onClick={() =>
                      void downloadFile(
                        `/inspections/${detail.token}/evidence/${e.id}`,
                        e.filename
                      )
                    }
                  >
                    Open
                  </button>
                </li>
              ))}

              {!detail.evidence.length && (
                <li className="py-5 text-center text-sm text-slate-400">
                  No evidence attached.
                </li>
              )}
            </ul>

            <label className="mt-4 flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-blue-200 bg-blue-50/50 px-4 py-3 text-sm font-semibold text-[#0B3B82] transition hover:border-blue-400 hover:bg-blue-50">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 5v14M5 12h14"
                />
              </svg>

              Attach evidence photo

              <input
                type="file"
                multiple
                className="hidden"
                onChange={uploadEvidence}
              />
            </label>
          </div>
        </section>
      </div>

      {/* Review Decision */}
      {isReviewer && (
        <section className="overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">
          <div className="border-b border-blue-50 bg-blue-50/40 px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white">
                <svg
                  className="h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 12l2 2 4-4"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 4h14v16H5z"
                  />
                </svg>
              </div>

              <div>
                <h2 className="text-sm font-semibold text-[#09265A]">
                  Review Decision
                </h2>
                <p className="text-xs text-slate-400">
                  Update the workflow status of this inspection
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-3 p-5 sm:flex-row sm:flex-wrap sm:items-center">
            <button
              className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-[#0B3B82] disabled:cursor-not-allowed disabled:opacity-60"
              disabled={busy}
              onClick={() => setWorkflow("reviewed")}
            >
              Mark reviewed
            </button>

            <button
              className="rounded-xl bg-[#0B3B82] px-5 py-2.5 text-xs font-semibold text-white shadow-md shadow-blue-900/10 transition hover:bg-[#092F6B] disabled:cursor-not-allowed disabled:opacity-60"
              disabled={busy}
              onClick={() => setWorkflow("approved")}
            >
              Approve
            </button>

            <button
              className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-[#0B3B82] disabled:cursor-not-allowed disabled:opacity-60"
              disabled={busy}
              onClick={() => setWorkflow("open")}
            >
              Reopen
            </button>

            {detail.reviewer && (
              <span className="text-xs text-slate-400 sm:ml-2">
                by {detail.reviewer.full_name} on{" "}
                {detail.reviewed_at || ""}
              </span>
            )}
          </div>
        </section>
      )}
    </div>
  );
}