import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { Page, User } from "../types";

export default function UsersPage() {
  const { user: me } = useAuth();
  const [data, setData] = useState<Page<User> | null>(null);
  const [form, setForm] = useState({ username: "", full_name: "", email: "", password: "", role: "officer" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setData(await api<Page<User>>("/users?page=1&size=100"));
    } catch {
      setData(null);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  if (me?.role !== "admin") {
    return <div className="card p-6 text-sm text-slate-500">Only administrators can manage users.</div>;
  }

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/users", { method: "POST", body: form });
      setForm({ username: "", full_name: "", email: "", password: "", role: "officer" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  };

  const toggleActive = async (u: User) => {
    await api(`/users/${u.id}`, { method: "PATCH", body: { is_active: !u.is_active } });
    await load();
  };

  const resetPassword = async (u: User) => {
    const next = window.prompt(`New password for ${u.username} (min 8 chars):`, "ChangeMe@123");
    if (!next) return;
    await api(`/users/${u.id}/reset-password`, { method: "POST", body: { new_password: next } });
    window.alert("Password updated");
  };

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gov-blue">User management (admin)</h1>

      <form className="card p-4 grid grid-cols-1 md:grid-cols-3 gap-3" onSubmit={create}>
        <input className="input" placeholder="Username *" value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })} required />
        <input className="input" placeholder="Full name *" value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        <input className="input" placeholder="Email" value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input className="input" type="password" placeholder="Password *" value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
          <option value="officer">Enforcement Officer</option>
          <option value="reviewer">Reviewer</option>
          <option value="admin">Admin</option>
        </select>
        <button className="btn-primary" disabled={busy}>Create user</button>
        {error && <p className="md:col-span-3 text-sm text-gov-bad">{error}</p>}
      </form>

      <div className="card overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr>
              <th className="th">Username</th>
              <th className="th">Full name</th>
              <th className="th">Email</th>
              <th className="th">Role</th>
              <th className="th">Status</th>
              <th className="th">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(data?.items || []).map((u) => (
              <tr key={u.id} className="hover:bg-slate-50">
                <td className="td font-medium">{u.username}</td>
                <td className="td">{u.full_name}</td>
                <td className="td text-xs">{u.email || "—"}</td>
                <td className="td capitalize">{u.role}</td>
                <td className="td">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${u.is_active ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}`}>
                    {u.is_active ? "active" : "disabled"}
                  </span>
                </td>
                <td className="td text-xs space-x-2">
                  <button className="text-gov-blue underline" onClick={() => void resetPassword(u)}>reset pwd</button>
                  <button className="text-gov-warn underline" onClick={() => void toggleActive(u)}>
                    {u.is_active ? "disable" : "enable"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}