import { ReactNode } from "react";

export default function StatCard({
  label,
  value,
  sub,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  sub?: string;
  tone?: "default" | "ok" | "bad" | "warn";
}) {
  const tones: Record<string, string> = {
    default: "text-[#12382c]",
    ok: "text-[#08734c]",
    bad: "text-gov-bad",
    warn: "text-gov-warn",
  };
  const accents: Record<string, string> = {
    default: "bg-emerald-50 text-[#08734c]",
    ok: "bg-emerald-50 text-[#08734c]",
    bad: "bg-red-50 text-red-600",
    warn: "bg-amber-50 text-amber-600",
  };
  return (
    <div className="flex min-h-[106px] items-start gap-3 p-4">
      <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${accents[tone]}`} aria-hidden="true">
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d={tone === "bad" ? "M12 8v5m0 4h.01M10.3 3.9 2.9 17a2 2 0 0 0 1.7 3h14.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" : tone === "warn" ? "M4 20v-7m5 7V4m5 16v-5m5 5V8" : "M6 3h8l4 4v14H6zM14 3v5h5M9 13h6m-6 4h6"} /></svg>
      </span>
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
        <p className={`mt-1 text-2xl font-bold ${tones[tone]}`}>{value}</p>
        {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
      </div>
    </div>
  );
}
