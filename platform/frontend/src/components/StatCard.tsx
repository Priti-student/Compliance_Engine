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
    default: "text-gov-blue",
    ok: "text-gov-ok",
    bad: "text-gov-bad",
    warn: "text-gov-warn",
  };
  return (
    <div className="card p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${tones[tone]}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}