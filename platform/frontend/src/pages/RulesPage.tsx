import { useEffect, useState } from "react";
import { api } from "../api/client";

interface RuleRow {
  rule_id: string;
  rule_reference?: string;
  title?: string;
  requirement?: string;
  field_name?: string;
  validation_logic?: { type?: string };
}

interface RulesDb {
  database_meta?: { title?: string; version?: string; last_updated?: string };
  mandatory_declarations?: RuleRow[];
  placement_and_manner_rules?: RuleRow[];
  wholesale_package_rules?: RuleRow[];
  font_size_and_legibility_rules?: Record<string, unknown>;
}

export default function RulesPage() {
  const [db, setDb] = useState<RulesDb | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<RulesDb>("/rules")
      .then(setDb)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card p-6 text-sm text-gov-bad">{error}</div>;
  if (!db) return <div className="p-10 text-sm text-slate-500">Loading rules…</div>;

  const renderRules = (rules: RuleRow[] | undefined) => (
    <div className="overflow-x-auto rounded border border-slate-200">
      <table className="w-full">
        <thead>
          <tr>
            <th className="th">Rule</th>
            <th className="th">Reference</th>
            <th className="th">Field</th>
            <th className="th">Title & requirement</th>
            <th className="th">Validation logic</th>
          </tr>
        </thead>
        <tbody>
          {(rules || []).map((r) => (
            <tr key={r.rule_id} className="align-top">
              <td className="td font-mono text-xs font-semibold whitespace-nowrap">{r.rule_id}</td>
              <td className="td text-xs whitespace-nowrap">{r.rule_reference || "—"}</td>
              <td className="td font-mono text-xs">{r.field_name || "—"}</td>
              <td className="td text-xs">
                <b>{r.title || ""}</b>
                <p className="text-slate-500 mt-0.5">{r.requirement || ""}</p>
              </td>
              <td className="td font-mono text-xs">{r.validation_logic?.type || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gov-blue">Digitized LMPC rule database</h1>
        <p className="text-xs text-slate-500 mt-1">
          {db.database_meta?.title} · v{db.database_meta?.version} · updated {db.database_meta?.last_updated}
        </p>
      </div>

      <section>
        <h2 className="font-semibold text-slate-700 mb-2">Mandatory declarations (Rule 6)</h2>
        {renderRules(db.mandatory_declarations)}
      </section>

      <section>
        <h2 className="font-semibold text-slate-700 mb-2">Placement & manner rules (Rule 8–9)</h2>
        {renderRules(db.placement_and_manner_rules)}
      </section>

      <section>
        <h2 className="font-semibold text-slate-700 mb-2">Font size & legibility (Rule 7)</h2>
        <pre className="bg-slate-50 border border-slate-200 rounded p-3 text-xs overflow-auto max-h-96">
          {JSON.stringify(db.font_size_and_legibility_rules ?? {}, null, 2)}
        </pre>
      </section>

      <section>
        <h2 className="font-semibold text-slate-700 mb-2">Wholesale package rules</h2>
        {renderRules(db.wholesale_package_rules)}
      </section>
    </div>
  );
}