/* eslint-disable react-hooks/set-state-in-effect */
import { useCallback, useEffect, useMemo, useState } from "react";
import { getInventory } from "../services/inventoryService";
import {
  calculateAssessmentsInBackground,
  downloadSustainabilityCsv,
  downloadSustainabilityExcel,
  downloadSustainabilityPdf,
  getAssessments,
  getMonthlySustainabilityTrends,
  getSustainabilitySummary,
} from "../services/sustainabilityService";

const emptySummary = {
  total_waste_kg: 0, co2_saved_kg: 0, water_saved_litres: 0,
  landfill_reduction_kg: 0, recoverable_material_kg: 0,
  waste_diversion_percentage: 0, average_circularity_score: 0,
  benchmark_diversion_percentage: 75, benchmark_status: "below", category_distribution: {},
};

const number = (value, digits = 0) => Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: digits });
const categoryTone = (category = "") => category.startsWith("Excellent") ? "bg-emerald-100 text-emerald-800" : category.startsWith("High") ? "bg-cyan-100 text-cyan-800" : category.startsWith("Moderate") ? "bg-amber-100 text-amber-800" : "bg-rose-100 text-rose-800";

function SustainabilityIntelligence({ role }) {
  const [summary, setSummary] = useState(emptySummary);
  const [assessments, setAssessments] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ search: "", fabric: "", status: "", from: "", to: "" });
  const [targets, setTargets] = useState(() => JSON.parse(localStorage.getItem("sustainabilityTargets") || '{"diversion":75,"circularity":75,"co2":100}'));

  const load = useCallback(async () => {
    setError("");
    try {
      const [summaryResponse, assessmentResponse, trendResponse, inventoryResponse] = await Promise.all([
        getSustainabilitySummary(), getAssessments(), getMonthlySustainabilityTrends(), getInventory(),
      ]);
      setSummary(summaryResponse.data);
      setAssessments(assessmentResponse.data);
      setTrends(trendResponse.data);
      setInventory(inventoryResponse.data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Sustainability analytics could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const missing = useMemo(() => {
    const assessed = new Set(assessments.map((item) => item.batch_id));
    return inventory.filter((item) => !assessed.has(item.waste_batch_id));
  }, [assessments, inventory]);

  const inventoryByBatch = useMemo(() => new Map(inventory.map((item) => [item.waste_batch_id, item])), [inventory]);
  const filteredAssessments = useMemo(() => assessments.filter((item) => {
    const batch = inventoryByBatch.get(item.batch_id) || {};
    const term = filters.search.toLowerCase();
    const date = String(batch.collection_date || "");
    return (!term || `${item.batch_id} ${batch.fabric_type || ""}`.toLowerCase().includes(term)) &&
      (!filters.fabric || batch.fabric_type === filters.fabric) && (!filters.status || batch.status === filters.status) &&
      (!filters.from || date >= filters.from) && (!filters.to || date <= filters.to);
  }), [assessments, filters, inventoryByBatch]);
  const fabrics = [...new Set(inventory.map((item) => item.fabric_type).filter(Boolean))].sort();
  const statuses = [...new Set(inventory.map((item) => item.status).filter(Boolean))].sort();
  const previousTrend = trends.length > 1 ? trends[trends.length - 2] : null;
  const currentTrend = trends.length ? trends[trends.length - 1] : null;

  const circularEconomy = useMemo(() => {
    const total = Math.max(summary.total_waste_kg, 1);
    const reused = assessments.filter((item) => item.recommended_action === "Direct reuse").reduce((sum, item) => sum + item.recoverable_material_kg, 0);
    const recovered = Math.max(summary.recoverable_material_kg - reused, 0);
    return [
      ["Reused", reused / total * 100, "bg-emerald-500"],
      ["Recycled / recoverable", recovered / total * 100, "bg-cyan-500"],
      ["Loss / disposal", Math.max(total - summary.recoverable_material_kg, 0) / total * 100, "bg-slate-400"],
    ];
  }, [assessments, summary]);

  const calculateMissing = async () => {
    setCalculating(true); setError("");
    try {
      await calculateAssessmentsInBackground();
      window.setTimeout(load, 1800);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "One or more batches could not be assessed. Check that quantity includes a valid positive value.");
    } finally { setCalculating(false); }
  };

  const download = async (kind) => {
    try {
      const response = kind === "pdf" ? await downloadSustainabilityPdf() : kind === "excel" ? await downloadSustainabilityExcel() : await downloadSustainabilityCsv();
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url; link.download = `sustainability-report.${kind === "excel" ? "xlsx" : kind}`;
      link.click(); URL.revokeObjectURL(url);
    } catch (requestError) { setError(requestError.response?.data?.detail || "The report could not be downloaded."); }
  };

  if (loading) return <section className="mt-6 rounded-3xl bg-white p-8 text-center font-bold text-slate-500 shadow-xl">Loading sustainability intelligence...</section>;

  return (
    <section className="mt-6 space-y-6" aria-labelledby="sustainability-title">
      <div className="overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-teal-950 to-emerald-800 p-6 text-white shadow-xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div><p className="text-xs font-bold uppercase tracking-[0.22em] text-emerald-300">Milestone 3</p><h2 id="sustainability-title" className="mt-2 text-3xl font-black">Sustainability Intelligence Engine</h2><p className="mt-2 text-sm text-slate-200">Environmental impact, weighted scoring, benchmarking and AI-guided recovery decisions.</p></div>
          <div className="flex flex-wrap gap-2">
            {missing.length > 0 && <button onClick={calculateMissing} disabled={calculating} className="rounded-2xl bg-emerald-400 px-4 py-3 text-sm font-black text-slate-950 disabled:opacity-60">{calculating ? "Calculating..." : `Assess ${missing.length} batch${missing.length === 1 ? "" : "es"}`}</button>}
            <button onClick={() => download("pdf")} disabled={!assessments.length} className="rounded-2xl bg-white/15 px-4 py-3 text-sm font-bold ring-1 ring-white/25 disabled:opacity-40">Download PDF</button>
            <button onClick={() => download("excel")} disabled={!assessments.length} className="rounded-2xl bg-white px-4 py-3 text-sm font-black text-teal-900 disabled:opacity-40">Download Excel</button>
            <button onClick={() => download("csv")} disabled={!assessments.length} className="rounded-2xl bg-white/15 px-4 py-3 text-sm font-bold ring-1 ring-white/25 disabled:opacity-40">CSV</button>
          </div>
        </div>
        {error && <p role="alert" className="mt-4 rounded-2xl bg-rose-500/20 px-4 py-3 text-sm font-bold text-rose-100 ring-1 ring-rose-300/30">{error}</p>}
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[["CO2 saved", `${number(summary.co2_saved_kg, 2)} kg`], ["Water saved", `${number(summary.water_saved_litres)} L`], ["Waste diverted", `${number(summary.waste_diversion_percentage, 1)}%`], ["Circularity score", `${number(summary.average_circularity_score, 1)} / 100`]].map(([label, value]) => <div key={label} className="rounded-2xl bg-white/10 p-4 ring-1 ring-white/15"><p className="text-xs font-semibold uppercase tracking-wider text-emerald-200">{label}</p><p className="mt-2 text-2xl font-black">{value}</p></div>)}
        </div>
      </div>

      <div className={`grid gap-6 ${role === "manager" ? "" : "lg:grid-cols-[1.3fr_0.7fr]"}`}>
        {role !== "manager" && <article className="rounded-3xl bg-white p-6 shadow-lg ring-1 ring-slate-200">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm font-bold text-teal-700">Analytics filters</p><h3 className="mt-1 text-xl font-black text-slate-950">Explore your sustainability data</h3></div><button onClick={() => setFilters({ search: "", fabric: "", status: "", from: "", to: "" })} className="text-sm font-bold text-cyan-700">Clear filters</button></div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5"><input value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} placeholder="Batch or fabric" className="rounded-xl border border-slate-200 px-3 py-2 text-sm"/><select value={filters.fabric} onChange={(e) => setFilters({ ...filters, fabric: e.target.value })} className="rounded-xl border border-slate-200 px-3 py-2 text-sm"><option value="">All fabrics</option>{fabrics.map((item) => <option key={item}>{item}</option>)}</select><select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} className="rounded-xl border border-slate-200 px-3 py-2 text-sm"><option value="">All statuses</option>{statuses.map((item) => <option key={item}>{item}</option>)}</select><input aria-label="From date" type="date" value={filters.from} onChange={(e) => setFilters({ ...filters, from: e.target.value })} className="rounded-xl border border-slate-200 px-3 py-2 text-sm"/><input aria-label="To date" type="date" value={filters.to} onChange={(e) => setFilters({ ...filters, to: e.target.value })} className="rounded-xl border border-slate-200 px-3 py-2 text-sm"/></div>
          <p className="mt-3 text-xs text-slate-500">Showing {filteredAssessments.length} of {assessments.length} assessed batches.</p>
        </article>}
        <article className="rounded-3xl bg-white p-6 shadow-lg ring-1 ring-slate-200"><p className="text-sm font-bold text-teal-700">Period comparison</p><h3 className="mt-1 text-xl font-black text-slate-950">Latest vs previous month</h3>{currentTrend ? <div className="mt-4 grid grid-cols-2 gap-3 text-sm"><div className="rounded-2xl bg-emerald-50 p-3"><span className="text-slate-500">CO2 change</span><b className="mt-1 block text-lg text-emerald-700">{previousTrend ? `${number(currentTrend.co2_saved_kg - previousTrend.co2_saved_kg, 1)} kg` : "First period"}</b></div><div className="rounded-2xl bg-cyan-50 p-3"><span className="text-slate-500">Circularity</span><b className="mt-1 block text-lg text-cyan-700">{number(currentTrend.average_circularity_score, 1)}</b></div></div> : <p className="mt-4 text-sm text-slate-500">No comparison data yet.</p>}</article>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <article className="rounded-3xl bg-white p-6 shadow-lg ring-1 ring-slate-200"><p className="text-sm font-bold text-teal-700">ESG targets & alerts</p><h3 className="mt-1 text-xl font-black text-slate-950">Performance thresholds</h3><div className="mt-4 space-y-3">{[["Diversion %", "diversion", summary.waste_diversion_percentage], ["Circularity", "circularity", summary.average_circularity_score], ["CO2 saved kg", "co2", summary.co2_saved_kg]].map(([label,key,current]) => <label key={key} className="grid grid-cols-[1fr_80px] items-center gap-3 text-sm"><span>{label} <b className={current >= targets[key] ? "text-emerald-700" : "text-amber-700"}>{current >= targets[key] ? "On target" : "Needs attention"}</b></span><input type="number" min="0" value={targets[key]} onChange={(e) => { const next = { ...targets, [key]: Number(e.target.value) }; setTargets(next); localStorage.setItem("sustainabilityTargets", JSON.stringify(next)); }} className="rounded-xl border border-slate-200 px-2 py-2"/></label>)}</div></article>
        <article className="rounded-3xl bg-white p-6 shadow-lg ring-1 ring-slate-200 lg:col-span-2"><div className="flex items-end justify-between gap-3"><div><p className="text-sm font-bold text-teal-700">Monthly trend</p><h3 className="mt-1 text-xl font-black text-slate-950">Carbon reduction trend</h3></div><span className="text-xs font-semibold text-slate-500">Last 6 months</span></div><div className="mt-5 grid gap-4 sm:grid-cols-2">{trends.slice(-6).map((trend) => { const max = Math.max(...trends.map((item) => item.co2_saved_kg), 1); return <div key={trend.month}><div className="flex justify-between text-xs"><span className="font-semibold text-slate-600">{trend.month}</span><b className="text-teal-700">{number(trend.co2_saved_kg, 1)} kg CO₂</b></div><div className="mt-2 h-3 rounded-full bg-slate-100"><div className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500" style={{ width: `${Math.max(trend.co2_saved_kg / max * 100, 4)}%` }} /></div></div>; })}{!trends.length && <p className="text-sm text-slate-500">Trend data appears after assessments are calculated.</p>}</div></article>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <article className="rounded-3xl bg-white p-6 shadow-lg ring-1 ring-slate-200"><p className="text-sm font-bold text-teal-700">Waste diversion analysis</p><h3 className="mt-1 text-xl font-black text-slate-950">{number(summary.total_waste_kg, 2)} kg total waste</h3><div className="mt-5 h-4 overflow-hidden rounded-full bg-slate-200"><div className="h-full bg-emerald-500" style={{ width: `${Math.min(summary.waste_diversion_percentage, 100)}%` }} /></div><div className="mt-4 grid grid-cols-2 gap-3 text-sm"><p><span className="block text-slate-500">Diverted</span><b>{number(summary.landfill_reduction_kg, 2)} kg</b></p><p><span className="block text-slate-500">Landfill</span><b>{number(Math.max(summary.total_waste_kg - summary.landfill_reduction_kg, 0), 2)} kg</b></p></div></article>
        <article className="rounded-3xl bg-white p-6 shadow-lg ring-1 ring-slate-200"><p className="text-sm font-bold text-teal-700">Circular economy analysis</p><h3 className="mt-1 text-xl font-black text-slate-950">Material outcomes</h3><div className="mt-4 space-y-4">{circularEconomy.map(([label, value, color]) => <div key={label}><div className="mb-1 flex justify-between text-sm"><span>{label}</span><b>{number(value, 1)}%</b></div><div className="h-2.5 rounded-full bg-slate-100"><div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(value, 100)}%` }} /></div></div>)}</div></article>
        <article className="rounded-3xl bg-white p-6 shadow-lg ring-1 ring-slate-200"><p className="text-sm font-bold text-teal-700">Sustainability benchmark</p><h3 className="mt-1 text-xl font-black text-slate-950">{summary.benchmark_status === "meeting" ? "Above industry benchmark" : "Below industry benchmark"}</h3><div className="mt-5 flex items-end gap-4"><div><p className="text-xs text-slate-500">Your diversion</p><p className="text-3xl font-black text-emerald-700">{number(summary.waste_diversion_percentage, 1)}%</p></div><div><p className="text-xs text-slate-500">Benchmark</p><p className="text-2xl font-black text-slate-500">{number(summary.benchmark_diversion_percentage, 1)}%</p></div></div><p className="mt-4 text-sm text-slate-600">Recoverable material: <b>{number(summary.recoverable_material_kg, 2)} kg</b></p></article>
      </div>

      <article id="circularity-decisions" className="scroll-mt-6 overflow-hidden rounded-3xl bg-white shadow-lg ring-1 ring-slate-200"><div className="border-b border-slate-100 p-6"><p className="text-sm font-bold text-teal-700">Waste scoring & AI recommendations</p><h3 className="mt-1 text-2xl font-black text-slate-950">Batch Circularity Decisions</h3><p className="mt-2 text-sm text-slate-500">A clear decision summary for every assessed waste batch.</p></div><div className="overflow-x-auto"><table className="min-w-[1180px] w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500"><tr><th className="p-4">Batch</th><th className="p-4">Recyclability</th><th className="p-4">Reuse</th><th className="p-4">Sustainability</th><th className="p-4">Material recovery</th><th className="p-4">Circularity</th><th className="p-4">Recommended decision</th><th className="p-4">Last calculated</th></tr></thead><tbody className="divide-y divide-slate-100">{filteredAssessments.map((item) => <tr key={item.id} className="align-top transition hover:bg-teal-50/40"><td className="p-4 font-black text-slate-900">{item.batch_id}</td><td className="p-4 font-bold text-cyan-700">{number(item.recyclability_score, 1)} / 100</td><td className="p-4 font-bold text-violet-700">{number(item.reuse_score, 1)} / 100</td><td className="p-4 font-bold text-emerald-700">{number(item.sustainability_score, 1)} / 100</td><td className="p-4"><b>{number(item.recoverable_material_kg, 2)} kg</b><span className="mt-1 block text-xs text-slate-500">{number(item.material_recovery_score, 1)}% recoverable</span></td><td className="p-4"><b className="text-xl text-slate-950">{number(item.circularity_score, 1)}</b><span className={`mt-2 block w-fit rounded-full px-2.5 py-1 text-[11px] font-bold ${categoryTone(item.circularity_category)}`}>{item.circularity_category}</span></td><td className="p-4"><b className="text-slate-900">{item.recommended_action}</b><span className="mt-1 block text-xs leading-5 text-slate-500">{item.recommended_processing_method}</span></td><td className="p-4 text-xs leading-5 text-slate-500">{new Date(item.updated_at).toLocaleString()}<span className="block">Calculated {item.audit_history?.length || 1} time(s)</span></td></tr>)}{!filteredAssessments.length && <tr><td colSpan="8" className="p-10 text-center text-slate-500">No assessed batches are available.</td></tr>}</tbody></table></div></article>
    </section>
  );
}

export default SustainabilityIntelligence;
