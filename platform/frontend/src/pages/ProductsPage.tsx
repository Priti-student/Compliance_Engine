import { useEffect, useState } from "react";
import { api } from "../api/client";
import Pagination from "../components/Pagination";
import type { Page, Product } from "../types";

export default function ProductsPage() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page<Product> | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    generic_name: "",
    brand: "",
    category: "",
    manufacturer: "",
    net_quantity_text: "",
    mrp: "",
  });
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      setData(
        await api<Page<Product>>(`/products?page=${page}&size=12`)
      );
    } catch {
      setData(null);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.generic_name.trim()) return;

    setBusy(true);

    try {
      await api("/products", {
        method: "POST",
        body: form,
      });

      setForm({
        generic_name: "",
        brand: "",
        category: "",
        manufacturer: "",
        net_quantity_text: "",
        mrp: "",
      });

      setShowForm(false);
      await load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">
            Product Management
          </p>

          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#09265A] sm:text-3xl">
            Product Master
          </h1>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Manage packaged commodity product information used for
            compliance inspections.
          </p>
        </div>

        <button
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#0B3B82] px-5 py-3 text-sm font-semibold text-white shadow-md shadow-blue-900/10 transition hover:bg-[#092F6B] sm:w-auto"
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? (
            <>
              <svg
                className="h-4 w-4"
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
              Close form
            </>
          ) : (
            <>
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  strokeLinecap="round"
                  d="M12 5v14M5 12h14"
                />
              </svg>
              Add product
            </>
          )}
        </button>
      </div>

      {/* Add Product Form */}
      {showForm && (
        <form
          className="overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm"
          onSubmit={create}
        >
          {/* Form Header */}
          <div className="border-b border-blue-50 bg-blue-50/40 px-5 py-4 sm:px-6">
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
                    d="M12 5v14M5 12h14"
                  />
                </svg>
              </div>

              <div>
                <h2 className="text-sm font-semibold text-[#09265A]">
                  Add New Product
                </h2>

                <p className="mt-0.5 text-xs text-slate-400">
                  Enter the packaged commodity details below
                </p>
              </div>
            </div>
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 gap-5 p-5 sm:p-6 md:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">
                Generic name <span className="text-red-500">*</span>
              </label>

              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                placeholder="e.g. Wheat Biscuits"
                value={form.generic_name}
                onChange={(e) =>
                  setForm({
                    ...form,
                    generic_name: e.target.value,
                  })
                }
                required
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">
                Brand
              </label>

              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                placeholder="e.g. Britannia"
                value={form.brand}
                onChange={(e) =>
                  setForm({
                    ...form,
                    brand: e.target.value,
                  })
                }
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">
                Category
              </label>

              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                placeholder="e.g. Food"
                value={form.category}
                onChange={(e) =>
                  setForm({
                    ...form,
                    category: e.target.value,
                  })
                }
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">
                Manufacturer
              </label>

              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                placeholder="Manufacturer name"
                value={form.manufacturer}
                onChange={(e) =>
                  setForm({
                    ...form,
                    manufacturer: e.target.value,
                  })
                }
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">
                Net quantity
              </label>

              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                placeholder="e.g. 500 g"
                value={form.net_quantity_text}
                onChange={(e) =>
                  setForm({
                    ...form,
                    net_quantity_text: e.target.value,
                  })
                }
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">
                MRP
              </label>

              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                placeholder="e.g. ₹50"
                value={form.mrp}
                onChange={(e) =>
                  setForm({
                    ...form,
                    mrp: e.target.value,
                  })
                }
              />
            </div>

            {/* Save */}
            <div className="md:col-span-2 lg:col-span-3">
              <button
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#0B3B82] px-5 py-3 text-sm font-semibold text-white shadow-md shadow-blue-900/10 transition hover:bg-[#092F6B] disabled:cursor-not-allowed disabled:opacity-60"
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
                    Saving product…
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
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M5 12l4 4L19 6"
                      />
                    </svg>
                    Save product
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Product Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {/* Table Header */}
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 sm:px-6">
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
                  d="M8 9h8M8 13h8M8 17h5"
                />
              </svg>
            </div>

            <div>
              <h2 className="text-sm font-semibold text-[#09265A]">
                Product Records
              </h2>

              <p className="mt-0.5 text-xs text-slate-400">
                Registered packaged commodities
              </p>
            </div>
          </div>

          {data && (
            <span className="rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-medium text-[#0B3B82]">
              {data.total} product{data.total !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px]">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/70">
                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Generic name
                </th>

                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Brand
                </th>

                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Category
                </th>

                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Net quantity
                </th>

                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  MRP
                </th>

                <th className="px-5 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Manufacturer
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {(data?.items || []).map((p) => (
                <tr
                  key={p.id}
                  className="transition hover:bg-blue-50/30"
                >
                  {/* Generic Name */}
                  <td className="px-5 py-4">
                    <div className="font-semibold text-[#09265A]">
                      {p.generic_name}
                    </div>
                  </td>

                  {/* Brand */}
                  <td className="px-5 py-4 text-sm text-slate-600">
                    {p.brand || "—"}
                  </td>

                  {/* Category */}
                  <td className="px-5 py-4">
                    {p.category ? (
                      <span className="inline-flex rounded-lg border border-blue-100 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
                        {p.category}
                      </span>
                    ) : (
                      <span className="text-sm text-slate-400">—</span>
                    )}
                  </td>

                  {/* Net Quantity */}
                  <td className="px-5 py-4 text-sm text-slate-600">
                    {p.net_quantity_text || "—"}
                  </td>

                  {/* MRP */}
                  <td className="px-5 py-4">
                    {p.mrp ? (
                      <span className="font-semibold text-[#0B3B82]">
                        {p.mrp}
                      </span>
                    ) : (
                      <span className="text-sm text-slate-400">—</span>
                    )}
                  </td>

                  {/* Manufacturer */}
                  <td className="px-5 py-4">
                    <span className="max-w-[180px] truncate text-xs text-slate-600">
                      {p.manufacturer || "—"}
                    </span>
                  </td>
                </tr>
              ))}

              {!data?.items?.length && (
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
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M5 5h14v14H5z"
                        />
                        <path
                          strokeLinecap="round"
                          d="M8 9h8M8 13h8"
                        />
                      </svg>
                    </div>

                    <p className="mt-3 text-sm font-medium text-slate-600">
                      No products yet
                    </p>

                    <p className="mt-1 text-xs text-slate-400">
                      Add a product to start building your product master.
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