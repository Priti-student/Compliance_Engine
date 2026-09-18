export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    compliant: "bg-emerald-100 text-emerald-800",
    non_compliant: "bg-red-100 text-red-800",
    needs_review: "bg-amber-100 text-amber-800",
    not_applicable: "bg-slate-200 text-slate-600",
    approved: "bg-emerald-100 text-emerald-800",
    reviewed: "bg-amber-100 text-amber-800",
    open: "bg-slate-200 text-slate-600",
  };
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${
        colors[status] || "bg-slate-100 text-slate-700"
      }`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    high: "bg-red-100 text-red-800",
    medium: "bg-amber-100 text-amber-800",
    low: "bg-slate-200 text-slate-600",
  };
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${colors[severity] || "bg-slate-100"}`}>
      {severity}
    </span>
  );
}