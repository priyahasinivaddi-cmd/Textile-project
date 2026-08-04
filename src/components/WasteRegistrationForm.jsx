import { useState } from "react";
import { createInventoryItem } from "../services/inventoryService";

const initialForm = { fabric_type: "", source: "", quantity: "", color: "", condition: "Reusable", collection_date: new Date().toISOString().slice(0, 10), status: "Pending", uploaded_by: "Manufacturer", assigned_to: "Recycling Facility" };

export default function WasteRegistrationForm({ onCreated }) {
  const [form, setForm] = useState(initialForm);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const field = (name) => ({ value: form[name], onChange: (event) => setForm({ ...form, [name]: event.target.value }) });
  const submit = async (event) => {
    event.preventDefault(); setSaving(true); setMessage("");
    try { await createInventoryItem(form); setForm(initialForm); setMessage("Waste batch registered successfully. Its ID was generated automatically."); await onCreated?.(); }
    catch (error) { setMessage(error.response?.data?.detail || "Waste registration failed. Please try again."); }
    finally { setSaving(false); }
  };
  return <form onSubmit={submit} className="mt-5 rounded-2xl border border-cyan-100 bg-cyan-50/60 p-5">
    <p className="text-xs font-bold uppercase tracking-widest text-cyan-700">Waste Registration</p><h3 className="mt-1 text-xl font-black text-slate-950">Register a new textile waste batch</h3><p className="mt-1 text-sm text-slate-600">The Waste Batch ID is generated when you save.</p>
    <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <input {...field("fabric_type")} className="rounded-xl border border-slate-200 bg-white px-4 py-3" placeholder="Fabric type" required /><input {...field("source")} className="rounded-xl border border-slate-200 bg-white px-4 py-3" placeholder="Source" required /><input {...field("quantity")} className="rounded-xl border border-slate-200 bg-white px-4 py-3" placeholder="Quantity, e.g. 100 kg" required /><input {...field("color")} className="rounded-xl border border-slate-200 bg-white px-4 py-3" placeholder="Color" required /><select {...field("condition")} className="rounded-xl border border-slate-200 bg-white px-4 py-3"><option>Reusable</option><option>Recyclable</option><option>Repairable</option><option>Damaged</option><option>Mixed</option><option>Contaminated</option></select><input {...field("collection_date")} type="date" className="rounded-xl border border-slate-200 bg-white px-4 py-3" required />
    </div>{message && <p className="mt-3 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-700">{message}</p>}<button disabled={saving} className="mt-4 rounded-2xl bg-cyan-700 px-5 py-3 font-bold text-white disabled:opacity-60">{saving ? "Registering..." : "Register Waste Batch"}</button>
  </form>;
}
