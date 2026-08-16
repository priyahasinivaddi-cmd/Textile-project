/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getModelInsights, getModelRegistry, promoteModel, syncModelRegistry } from "../services/platformService";

const metric = (metrics, key) => metrics?.[key] ?? metrics?.usage?.["macro avg"]?.[key.replace("macro_", "")] ?? null;
export default function ModelInsights() {
  const [models, setModels] = useState([]); const [registry, setRegistry] = useState([]); const [message, setMessage] = useState("");
  const load = async () => { const [insights, registered] = await Promise.all([getModelInsights(), getModelRegistry()]); setModels(insights.data.models); setRegistry(registered.data); };
  useEffect(() => { load(); }, []);
  const sync = async () => { const { data } = await syncModelRegistry(); setMessage(`${data.created} artifact(s) registered.`); await load(); };
  const promote = async id => { try { await promoteModel(id); setMessage("Model promoted to production."); await load(); } catch (error) { setMessage(error.response?.data?.detail || "Promotion failed."); } };
  return <main className="min-h-screen bg-slate-50 px-4 py-8"><div className="mx-auto max-w-7xl">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-sm font-black uppercase tracking-wider text-cyan-700">Authorized model operations</p><h1 className="text-3xl font-black text-slate-950">AI Model Insights</h1></div><div className="flex gap-2"><button onClick={sync} className="rounded-xl bg-cyan-700 px-4 py-2 font-bold text-white">Sync artifacts</button><Link to="/dashboard" className="rounded-xl bg-slate-900 px-4 py-2 font-bold text-white">Dashboard</Link></div></div>
    {message && <p role="status" className="mt-4 rounded-xl bg-amber-50 p-3 text-sm font-bold text-amber-800">{message}</p>}
    <section className="mt-6 grid gap-5 lg:grid-cols-3">{models.map(model => <article key={model.model_key} className="rounded-3xl bg-white p-6 shadow ring-1 ring-slate-200"><div className="flex justify-between gap-3"><h2 className="font-black text-slate-950">{model.architecture}</h2><span className={`h-fit rounded-full px-2 py-1 text-xs font-black ${model.quality_gate_passed ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>{model.quality_gate_passed ? "Gate passed" : "Development"}</span></div><dl className="mt-4 space-y-2 text-sm"><div><dt className="text-slate-500">Version</dt><dd className="break-all font-bold">{model.version}</dd></div><div><dt className="text-slate-500">Dataset</dt><dd className="font-bold">{model.dataset}</dd></div><div><dt className="text-slate-500">Macro F1</dt><dd className="text-2xl font-black text-cyan-700">{metric(model.metrics, "macro_f1") != null ? Number(metric(model.metrics, "macro_f1")).toFixed(3) : "See task metrics"}</dd></div></dl></article>)}</section>
    <section className="mt-6 rounded-3xl bg-white p-6 shadow ring-1 ring-slate-200"><h2 className="text-2xl font-black">Model Registry</h2><div className="mt-4 overflow-x-auto"><table className="min-w-full text-left text-sm"><thead><tr className="text-slate-500"><th className="p-3">Model</th><th className="p-3">Version</th><th className="p-3">Stage</th><th className="p-3">Action</th></tr></thead><tbody>{registry.map(item => <tr key={item.id} className="border-t"><td className="p-3 font-bold">{item.model_key}</td><td className="p-3">{item.version}</td><td className="p-3">{item.stage}</td><td className="p-3"><button disabled={item.active} onClick={() => promote(item.id)} className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-bold text-white disabled:opacity-40">{item.active ? "Production" : "Promote"}</button></td></tr>)}</tbody></table></div></section>
  </div></main>;
}
