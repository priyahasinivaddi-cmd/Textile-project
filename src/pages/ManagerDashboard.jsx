import { useEffect, useMemo, useState } from "react";
import { getInventory } from "../services/inventoryService";

function ManagerDashboard() {
  const [batches, setBatches] = useState([]);

  useEffect(() => {
    getInventory().then((response) => setBatches(response.data));
  }, []);

  const recycled = batches.filter((batch) => batch.status === "Recycled").length;
  const divertedPercent = batches.length ? Math.round((recycled / batches.length) * 100) : 0;
  const co2Savings = recycled * 24;

  const byStatus = useMemo(() => {
    return batches.reduce((summary, batch) => {
      summary[batch.status] = (summary[batch.status] || 0) + 1;
      return summary;
    }, {});
  }, [batches]);

  return (
    <section className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        {[
          ["Total Batches", batches.length],
          ["Waste Diverted", `${divertedPercent}%`],
          ["CO2 Savings", `${co2Savings}kg`],
          ["ESG Reports", 4],
        ].map(([label, value]) => (
          <div key={label} className="rounded-3xl bg-white p-5 shadow-md ring-1 ring-slate-200">
            <p className="text-sm font-semibold text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-black text-teal-700">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal-600">
            Waste Data Overview
          </p>
          <h2 className="mt-1 text-2xl font-black text-slate-950">
            Read-only Batch Monitoring
          </h2>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="p-3">Batch</th>
                  <th className="p-3">Fabric</th>
                  <th className="p-3">Quantity</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((batch) => (
                  <tr key={batch.id} className="border-t border-slate-100">
                    <td className="p-3 font-bold">{batch.waste_batch_id}</td>
                    <td className="p-3">{batch.fabric_type}</td>
                    <td className="p-3">{batch.quantity}</td>
                    <td className="p-3">{batch.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-3xl bg-gradient-to-br from-teal-600 to-lime-500 p-6 text-white shadow-xl">
          <h2 className="text-2xl font-black">Metrics & Trends</h2>
          <div className="mt-5 space-y-4">
            {Object.entries(byStatus).map(([status, count]) => (
              <div key={status}>
                <div className="flex justify-between text-sm font-bold">
                  <span>{status}</span>
                  <span>{count}</span>
                </div>
                <div className="mt-2 h-3 rounded-full bg-white/20">
                  <div
                    className="h-3 rounded-full bg-white"
                    style={{ width: `${Math.max((count / Math.max(batches.length, 1)) * 100, 8)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {["Waste Diversion Analytics", "Carbon Reduction Reports", "ESG Reporting"].map((title) => (
          <div key={title} className="rounded-3xl bg-white p-6 shadow-lg ring-1 ring-slate-200">
            <h3 className="text-lg font-black text-slate-950">{title}</h3>
            <p className="mt-2 text-sm text-slate-600">
              Uses shared batch status and recovery data to monitor environmental impact.
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default ManagerDashboard;
