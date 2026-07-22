/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getInventory, updateInventoryItem } from "../services/inventoryService";

function OperatorDashboard() {
  const [batches, setBatches] = useState([]);
  const [filters, setFilters] = useState({
    fabric_type: "",
    quantity: "",
    condition: "",
  });

  const loadBatches = async () => {
    const response = await getInventory();
    setBatches(response.data);
  };

  useEffect(() => {
    loadBatches();
  }, []);

  const filteredBatches = useMemo(() => {
    return batches.filter((batch) => {
      return (
        batch.fabric_type.toLowerCase().includes(filters.fabric_type.toLowerCase()) &&
        batch.quantity.toLowerCase().includes(filters.quantity.toLowerCase()) &&
        batch.condition.toLowerCase().includes(filters.condition.toLowerCase())
      );
    });
  }, [batches, filters]);

  const updateStatus = async (batch, status) => {
    await updateInventoryItem(batch.id, { status });
    await loadBatches();
  };

  return (
    <section className="space-y-6">

      {/* ── AI Analysis Quick Action ── */}
      <Link
        to="/analyze"
        className="group flex items-center gap-4 rounded-3xl bg-gradient-to-br from-cyan-600 to-emerald-600 p-5 text-white shadow-lg shadow-cyan-200 transition hover:-translate-y-0.5"
      >
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/20 text-2xl">♻️</div>
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-white/70">AI Pipeline</p>
          <h3 className="text-lg font-black">Textile Waste Intelligence Platform</h3>
          <p className="text-xs text-white/80">Analyse fabric images → get material classification &amp; recycling recommendations</p>
        </div>
        <svg className="ml-auto h-5 w-5 text-white/60 transition group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </Link>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          ["Available Waste", batches.length],
          ["Incoming Collections", batches.filter((b) => b.status === "Pickup Requested").length],
          ["Processing", batches.filter((b) => b.status === "Processing").length],
        ].map(([label, value]) => (
          <div key={label} className="rounded-3xl bg-white p-5 shadow-md ring-1 ring-slate-200">
            <p className="text-sm font-semibold text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-black text-emerald-700">{value}</p>
          </div>
        ))}
      </div>

      <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-600">
              Waste Inventory
            </p>
            <h2 className="mt-1 text-2xl font-black text-slate-950">
              Available Manufacturer Batches
            </h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Fabric type" value={filters.fabric_type} onChange={(e) => setFilters({ ...filters, fabric_type: e.target.value })} />
            <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Quantity" value={filters.quantity} onChange={(e) => setFilters({ ...filters, quantity: e.target.value })} />
            <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Condition" value={filters.condition} onChange={(e) => setFilters({ ...filters, condition: e.target.value })} />
          </div>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {filteredBatches.map((batch) => (
            <article key={batch.id} className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500">
                    {batch.waste_batch_id}
                  </p>
                  <h3 className="mt-1 text-xl font-black text-slate-950">
                    {batch.fabric_type} waste
                  </h3>
                  <p className="text-sm text-slate-600">
                    {batch.quantity} from {batch.source}
                  </p>
                </div>
                <span className="rounded-full bg-cyan-100 px-3 py-1 text-xs font-bold text-cyan-700">
                  {batch.condition}
                </span>
              </div>
              <div className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
                <p>Color: {batch.color}</p>
                <p>Collection: {batch.collection_date}</p>
                <p>Status: {batch.status}</p>
                <p>Assigned: {batch.assigned_to}</p>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button onClick={() => updateStatus(batch, "Accepted")} className="rounded-xl bg-emerald-600 px-3 py-2 text-sm font-bold text-white">Accept</button>
                <button onClick={() => updateStatus(batch, "Collected")} className="rounded-xl bg-sky-600 px-3 py-2 text-sm font-bold text-white">Collected</button>
                <button onClick={() => updateStatus(batch, "Processing")} className="rounded-xl bg-violet-600 px-3 py-2 text-sm font-bold text-white">Processing</button>
                <button onClick={() => updateStatus(batch, "Recycled")} className="rounded-xl bg-slate-950 px-3 py-2 text-sm font-bold text-white">Recycled</button>
              </div>
            </article>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl bg-gradient-to-br from-emerald-600 to-cyan-600 p-6 text-white shadow-xl">
          <h2 className="text-2xl font-black">Recycling Opportunities</h2>
          <div className="mt-4 grid gap-3">
            {batches.slice(0, 4).map((batch) => (
              <div key={batch.id} className="rounded-2xl bg-white/15 p-4 ring-1 ring-white/20">
                <p className="font-bold">{batch.fabric_type} can be routed for reuse or fiber recovery.</p>
                <p className="text-sm text-white/80">{batch.waste_batch_id} · {batch.condition}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <h2 className="text-2xl font-black text-slate-950">Analytics</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="font-bold">Processing Analytics</p>
              <p className="text-sm text-slate-500">{batches.filter((b) => b.status === "Processing").length} active batch(es)</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="font-bold">Recovery Statistics</p>
              <p className="text-sm text-slate-500">{batches.filter((b) => b.status === "Recycled").length} recycled batch(es)</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default OperatorDashboard;
