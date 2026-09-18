import { ChangeEvent, DragEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const DEMO_SOURCES = [
  "package_001.json",
  "package_002.json",
  "package_003.json",
  "ProductLays.json",
  "Wheet.json",
];

export default function ScanPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [productName, setProductName] = useState("");
  const [category, setCategory] = useState("");
  const [brand, setBrand] = useState("");
  const [remarks, setRemarks] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [demoSource, setDemoSource] = useState(DEMO_SOURCES[0]);

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  };

  const onPick = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const submit = async () => {
    if (!file) {
      setError("Choose or drop a package image first");
      return;
    }

    setBusy(true);
    setError("");

    const form = new FormData();
    form.append("file", file);
    form.append(
      "metadata",
      JSON.stringify({
        product_name: productName || undefined,
        category: category || undefined,
        brand: brand || undefined,
        remarks: remarks || undefined,
      })
    );

    try {
      const inspection = await api<{ token: string }>("/inspections", {
        method: "POST",
        body: form,
      });

      navigate(`/inspections/${inspection.token}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setBusy(false);
    }
  };

  const importDemo = async () => {
    setBusy(true);
    setError("");

    try {
      const out = await api<{ token: string }>("/inspections/from-demo", {
        method: "POST",
        body: { source: demoSource },
      });

      navigate(`/inspections/${out.token}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo import failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="w-full max-w-5xl space-y-6">
      {/* Page Header */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">
          Compliance Inspection
        </p>

        <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#09265A] sm:text-3xl">
          Scan a Packaged Commodity
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
          Upload a package or label photograph to perform an automated
          Legal Metrology compliance inspection.
        </p>
      </div>

      {/* Upload Card */}
      <div
        className={`relative overflow-hidden rounded-2xl border-2 border-dashed bg-white p-6 text-center shadow-sm transition-all sm:p-10 ${
          dragOver
            ? "border-blue-600 bg-blue-50/70 shadow-md"
            : "border-slate-200 hover:border-blue-300"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
      >
        {/* Decorative circles */}
        <div className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full bg-blue-50" />
        <div className="pointer-events-none absolute -bottom-12 -left-12 h-32 w-32 rounded-full bg-slate-50" />

        <div className="relative">
          {/* Upload Icon */}
          <div
            className={`mx-auto flex h-16 w-16 items-center justify-center rounded-2xl transition ${
              dragOver
                ? "bg-blue-600 text-white"
                : "bg-blue-50 text-blue-700"
            }`}
          >
            <svg
              className="h-8 w-8"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 16.5V19a2 2 0 002 2h12a2 2 0 002-2v-2.5"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 3v12"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M7.5 7.5L12 3l4.5 4.5"
              />
            </svg>
          </div>

          <p className="mt-5 text-base font-semibold text-[#09265A]">
            Upload package or label photograph
          </p>

          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
            Drop your image here, or{" "}
            <label className="cursor-pointer font-semibold text-blue-600 underline decoration-blue-200 underline-offset-4 hover:text-blue-800">
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={onPick}
              />
              browse files
            </label>
          </p>

          <p className="mt-2 text-xs text-slate-400">
            Supported image formats · JPG, JPEG, PNG
          </p>

          {file && (
            <div className="mx-auto mt-5 flex max-w-md items-center gap-3 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-left">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white">
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
                    d="M4 5a2 2 0 012-2h8l6 6v10a2 2 0 01-2 2H6a2 2 0 01-2-2V5z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M14 3v6h6"
                  />
                </svg>
              </div>

              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-[#09265A]">
                  {file.name}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">
                  {(file.size / 1024).toFixed(0)} KB
                </p>
              </div>
            </div>
          )}

          <p className="mt-4 text-xs text-slate-400">
            Officer:{" "}
            <span className="font-medium text-slate-600">
              {user?.full_name || user?.username}
            </span>
          </p>
        </div>
      </div>

      {/* Metadata Card */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
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
                  d="M4 6a2 2 0 012-2h12a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6z"
                />
                <path
                  strokeLinecap="round"
                  d="M8 9h8M8 13h8M8 17h4"
                />
              </svg>
            </div>

            <div>
              <h2 className="font-semibold text-[#09265A]">
                Optional Scan Metadata
              </h2>
              <p className="mt-0.5 text-xs text-slate-400">
                Add additional product information if available
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-5 p-5 sm:p-6">
          <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">
                Product name
              </label>

              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                placeholder="e.g. Wheat Biscuits"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">
                Category
              </label>

              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="food / cosmetics / electronics"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">
                Brand
              </label>

              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                placeholder="e.g. Britannia"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-600">
              Officer remarks
            </label>

            <textarea
              className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
              rows={3}
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="Capture location, sample details…"
            />
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <svg
            className="mt-0.5 h-5 w-5 shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="9" />
            <path
              strokeLinecap="round"
              d="M12 8v5M12 16h.01"
            />
          </svg>

          <p>{error}</p>
        </div>
      )}

      {/* Scan Button */}
      <button
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#0B3B82] px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-900/15 transition hover:bg-[#092F6B] disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        disabled={busy}
        onClick={submit}
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
                d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z"
              />
            </svg>
            Running compliance scan…
          </>
        ) : (
          <>
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
                d="M4 7V5a1 1 0 011-1h2M17 4h2a1 1 0 011 1v2M20 17v2a1 1 0 01-1 1h-2M7 20H5a1 1 0 01-1-1v-2"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8 12h8M12 8v8"
              />
            </svg>
            Scan & generate report
          </>
        )}
      </button>

      {/* Demo / Offline Mode */}
      <div className="overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">
        <div className="border-b border-blue-50 bg-blue-50/50 px-5 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-blue-700 shadow-sm">
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
                  d="M12 3v18M3 12h18"
                />
                <circle cx="12" cy="12" r="9" />
              </svg>
            </div>

            <div>
              <h2 className="font-semibold text-[#09265A]">
                Training / Offline Mode
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                Use a stored demo compliance report when the CV/OCR engine is
                offline.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:p-6">
          <select
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 sm:w-auto"
            value={demoSource}
            onChange={(e) => setDemoSource(e.target.value)}
          >
            {DEMO_SOURCES.map((s) => (
              <option key={s} value={s}>
                {s.replace(".json", "")}
              </option>
            ))}
          </select>

          <button
            className="rounded-xl border border-blue-200 bg-white px-5 py-2.5 text-sm font-semibold text-[#0B3B82] transition hover:border-blue-300 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={busy}
            onClick={importDemo}
          >
            Import demo
          </button>
        </div>
      </div>
    </div>
  );
}