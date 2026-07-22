/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  createInventoryItem,
  deleteInventoryItem,
  getInventory,
  updateInventoryItem,
} from "../services/inventoryService";

const emptyForm = {
  fabric_type: "",
  source: "",
  quantity: "",
  color: "",
  condition: "Reusable",
  collection_date: new Date().toISOString().slice(0, 10),
  status: "Pending",
  uploaded_by: "Manufacturer",
  assigned_to: "Recycling Facility",
};

function ManufacturerDashboard() {
  const [batches, setBatches] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState("");

  const loadBatches = async () => {
    const response = await getInventory();
    setBatches(response.data);
  };

  useEffect(() => {
    loadBatches();
  }, []);

  const sourceSummary = useMemo(() => {
    return batches.reduce((summary, batch) => {
      summary[batch.source] = (summary[batch.source] || 0) + 1;
      return summary;
    }, {});
  }, [batches]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");

    if (editingId) {
      await updateInventoryItem(editingId, form);
      setMessage("Batch updated successfully.");
    } else {
      await createInventoryItem(form);
      setMessage("Waste batch registered successfully.");
    }

    setForm(emptyForm);
    setEditingId(null);
    await loadBatches();
  };

  const editBatch = (batch) => {
    setEditingId(batch.id);
    setForm({
      fabric_type: batch.fabric_type,
      source: batch.source,
      quantity: batch.quantity,
      color: batch.color,
      condition: batch.condition,
      collection_date: batch.collection_date,
      status: batch.status,
      uploaded_by: batch.uploaded_by,
      assigned_to: batch.assigned_to,
    });
  };

  const requestPickup = async (batch) => {
    await updateInventoryItem(batch.id, { status: "Pickup Requested" });
    await loadBatches();
  };

  const removeBatch = async (id) => {
    await deleteInventoryItem(id);
    await loadBatches();
  };

  return (
    <section className="space-y-6">

      {/* ── AI Analysis Quick Actions ── */}
      <div className="grid gap-4 md:grid-cols-3">
        <Link
          to="/upload"
          className="group flex items-center gap-4 rounded-3xl bg-gradient-to-br from-cyan-600 to-emerald-600 p-5 text-white shadow-lg shadow-cyan-200 transition hover:-translate-y-0.5 hover:shadow-cyan-300"
        >
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/20 text-2xl">
            🔬
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-white/70">AI Pipeline</p>
            <h3 className="text-lg font-black">Upload &amp; Analyse Waste</h3>
            <p className="text-xs text-white/80">Upload textile image → AI classifies material &amp; waste</p>
          </div>
          <svg className="ml-auto h-5 w-5 text-white/60 transition group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>

        <Link
          to="/composition-prediction"
          className="group flex items-center gap-4 rounded-3xl bg-gradient-to-br from-violet-600 to-cyan-600 p-5 text-white shadow-lg shadow-violet-200 transition hover:-translate-y-0.5"
        >
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/20 text-2xl">
            %
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-white/70">Trained model</p>
            <h3 className="text-lg font-black">Predict Composition</h3>
            <p className="text-xs text-white/80">Estimate fibre percentages from a fabric image</p>
          </div>
          <svg className="ml-auto h-5 w-5 text-white/60 transition group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>

        <Link
          to="/analyze"
          className="group flex items-center gap-4 rounded-3xl bg-gradient-to-br from-slate-800 to-cyan-900 p-5 text-white shadow-lg ring-1 ring-slate-700 transition hover:-translate-y-0.5"
        >
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-2xl">
            ♻️
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Standalone</p>
            <h3 className="text-lg font-black">Waste Intelligence Platform</h3>
            <p className="text-xs text-slate-400">Analyse images without saving to inventory</p>
          </div>
          <svg className="ml-auto h-5 w-5 text-slate-500 transition group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {[
          ["Uploaded Batches", batches.length],
          ["Pending", batches.filter((b) => b.status === "Pending").length],
          ["Collected", batches.filter((b) => b.status === "Collected").length],
          ["Recycled", batches.filter((b) => b.status === "Recycled").length],
        ].map(([label, value]) => (
          <div key={label} className="rounded-3xl bg-white p-5 shadow-md ring-1 ring-slate-200">
            <p className="text-sm font-semibold text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-black text-cyan-700">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <form onSubmit={handleSubmit} className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <div className="mb-5">
            <p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-600">
              Waste Registration
            </p>
            <h2 className="mt-1 text-2xl font-black text-slate-950">
              {editingId ? "Edit Waste Batch" : "Create Waste Batch"}
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Batch ID is generated automatically when saved.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Fabric Type" value={form.fabric_type} onChange={(e) => setForm({ ...form, fabric_type: e.target.value })} required />
            <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Source factory/unit" value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} required />
            <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Quantity, e.g. 100kg" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} required />
            <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Color" value={form.color} onChange={(e) => setForm({ ...form, color: e.target.value })} required />
            <select className="rounded-2xl border border-slate-200 px-4 py-3" value={form.condition} onChange={(e) => setForm({ ...form, condition: e.target.value })}>
              <option>Reusable</option>
              <option>Recyclable</option>
              <option>Damaged</option>
              <option>Mixed</option>
            </select>
            <input className="rounded-2xl border border-slate-200 px-4 py-3" type="date" value={form.collection_date} onChange={(e) => setForm({ ...form, collection_date: e.target.value })} required />
          </div>

          {message && <p className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-700">{message}</p>}

          <button className="mt-5 w-full rounded-2xl bg-gradient-to-r from-cyan-600 to-emerald-500 px-5 py-3 font-black text-white shadow-lg shadow-cyan-200 transition hover:-translate-y-0.5">
            {editingId ? "Save Changes" : "Register Waste"}
          </button>
        </form>

        <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-cyan-600">
            Batch Management
          </p>
          <h2 className="mt-1 text-2xl font-black text-slate-950">Uploaded Batches</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="p-3">Batch</th>
                  <th className="p-3">Fabric</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((batch) => (
                  <tr key={batch.id} className="border-t border-slate-100">
                    <td className="p-3 font-bold text-slate-900">{batch.waste_batch_id}</td>
                    <td className="p-3">{batch.fabric_type}</td>
                    <td className="p-3">
                      <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-700">
                        {batch.status}
                      </span>
                    </td>
                    <td className="flex flex-wrap gap-2 p-3">
                      <button onClick={() => editBatch(batch)} className="rounded-xl bg-sky-100 px-3 py-2 font-bold text-sky-700">Edit</button>
                      <button onClick={() => requestPickup(batch)} className="rounded-xl bg-emerald-100 px-3 py-2 font-bold text-emerald-700">Pickup</button>
                      <button onClick={() => removeBatch(batch.id)} className="rounded-xl bg-rose-100 px-3 py-2 font-bold text-rose-700">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <h2 className="text-2xl font-black text-slate-950">Waste Source Tracking</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {Object.entries(sourceSummary).map(([source, count]) => (
              <div key={source} className="rounded-2xl bg-slate-50 p-4">
                <p className="font-bold text-slate-900">{source}</p>
                <p className="text-sm text-slate-500">{count} batch(es)</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-gradient-to-br from-slate-950 to-cyan-800 p-6 text-white shadow-xl">
          <h2 className="text-2xl font-black">Analytics</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {["Production Waste Analysis", "Circular Economy Insights", "Material Recovery Reports", "Sustainability Performance"].map((item) => (
              <div key={item} className="rounded-2xl bg-white/10 p-4 font-semibold ring-1 ring-white/15">
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default ManufacturerDashboard;
