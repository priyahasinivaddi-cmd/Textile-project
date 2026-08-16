/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from "react";
import { getInventory } from "../services/inventoryService";
import { getSystemStatus } from "../services/userService";
import { getUsers } from "../services/userService";
import { downloadDedicatedReport } from "../services/sustainabilityService";

function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [batches, setBatches] = useState([]);
  const [system, setSystem] = useState(null);
  const [reportBusy, setReportBusy] = useState("");

  const loadData = async () => {
    const [inventoryResponse, systemResponse, userResponse] = await Promise.all([
      getInventory(),
      getSystemStatus(),
      getUsers(),
    ]);
    setBatches(inventoryResponse.data);
    setSystem(systemResponse.data);
    setUsers(userResponse.data);
  };

  useEffect(() => {
    loadData();
  }, []);

  const totalRecycled = batches.filter((batch) => batch.status === "Recycled").length;
  const totalGenerated = batches.length;

  const downloadReport = async (type, format) => {
    const key = `${type}-${format}`;
    setReportBusy(key);
    try {
      const response = await downloadDedicatedReport(type, format);
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${type}-report.${format === "excel" ? "xlsx" : "pdf"}`;
      link.click();
      URL.revokeObjectURL(url);
    } finally { setReportBusy(""); }
  };

  return (
    <section className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        {[
          ["Total Waste Batches", totalGenerated],
          ["Processing", batches.filter((batch) => batch.status === "Processing").length],
          ["Total Recycled", totalRecycled],
        ].map(([label, value]) => (
          <div key={label} className="rounded-3xl bg-white p-5 shadow-md ring-1 ring-slate-200">
            <p className="text-sm font-semibold text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-black text-indigo-700">{value}</p>
          </div>
        ))}
      </div>

      <section className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
        <div><p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-600">Read-only directory</p><h2 className="mt-1 text-2xl font-black text-slate-950">Registered users</h2><p className="mt-1 text-sm text-slate-500">Roles are chosen during registration. This directory does not change or delete accounts.</p></div>
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full text-left text-sm"><thead className="text-slate-500"><tr><th className="p-3">Name</th><th className="p-3">Email</th><th className="p-3">Role</th><th className="p-3">Organization</th></tr></thead>
            <tbody>{users.map((user) => <tr key={user.id} className="border-t border-slate-100"><td className="p-3 font-bold text-slate-900">{user.name}</td><td className="p-3">{user.email}</td><td className="p-3 capitalize">{user.role}</td><td className="p-3">{user.organization_id || "—"}</td></tr>)}{!users.length && <tr><td colSpan="4" className="p-8 text-center text-slate-500">No registered users.</td></tr>}</tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-3xl bg-gradient-to-br from-indigo-700 to-slate-950 p-6 text-white shadow-xl">
          <h2 className="text-2xl font-black">Platform Analytics</h2>
          <div className="mt-4 space-y-3">
            <div className="flex justify-between rounded-2xl bg-white/10 p-3"><span>Registered batches</span><span className="font-black">{totalGenerated}</span></div>
            <div className="flex justify-between rounded-2xl bg-white/10 p-3"><span>Processing</span><span className="font-black">{batches.filter((batch) => batch.status === "Processing").length}</span></div>
            <div className="flex justify-between rounded-2xl bg-white/10 p-3"><span>Recycled</span><span className="font-black">{totalRecycled}</span></div>
          </div>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <h2 className="text-2xl font-black text-slate-950">System Monitoring</h2>
          <div className="mt-4 space-y-3">
            <p className="rounded-2xl bg-emerald-50 p-4 font-bold text-emerald-700">
              API: {system?.api_status || "checking"} · Database: {system?.database_status || "checking"}
            </p>
            <p className="rounded-2xl bg-slate-50 p-4 font-bold text-slate-700">
              Uptime: {Math.floor((system?.uptime_seconds || 0) / 60)} min · Assessment coverage: {system?.assessment_coverage_percentage || 0}%
            </p>
            <p className="text-xs text-slate-500">Last checked: {system?.checked_at ? new Date(system.checked_at).toLocaleString() : "Checking…"}</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <h2 className="text-2xl font-black text-slate-950">Report Management</h2>
          <div className="mt-4 space-y-3">
            {[["waste-classification", "Waste classification"], ["recycling", "Recycling"], ["sustainability", "Sustainability"], ["environmental-impact", "Environmental impact"], ["circular-economy", "Circular economy"], ["esg", "ESG sustainability"]].map(([type, label]) => (
              <div key={type} className="rounded-2xl bg-slate-100 p-3">
                <p className="font-bold text-slate-800">{label}</p>
                <div className="mt-2 flex gap-2"><button disabled={!!reportBusy} onClick={() => downloadReport(type, "pdf")} className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-bold text-white">{reportBusy === `${type}-pdf` ? "Preparing…" : "PDF"}</button><button disabled={!!reportBusy} onClick={() => downloadReport(type, "excel")} className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-bold text-white">{reportBusy === `${type}-excel` ? "Preparing…" : "Excel"}</button></div>
              </div>
            ))}
            <div className="flex justify-between rounded-2xl bg-white/10 p-3"><span>Assessment coverage</span><span className="font-black">{system?.assessment_coverage_percentage || 0}%</span></div>
            <div className="flex justify-between rounded-2xl bg-white/10 p-3"><span>Processing batches</span><span className="font-black">{batches.filter((batch) => batch.status === "Processing").length}</span></div>
            <div className="flex justify-between rounded-2xl bg-white/10 p-3"><span>Waste diversion progress</span><span className="font-black">{totalGenerated ? Math.round(totalRecycled / totalGenerated * 100) : 0}%</span></div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default AdminDashboard;
