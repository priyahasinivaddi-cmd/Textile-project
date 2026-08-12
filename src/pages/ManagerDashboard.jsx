/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useState } from "react";
import { getInventory } from "../services/inventoryService";
import { getAssessments } from "../services/sustainabilityService";
import ReportExportPanel from "../components/ReportExportPanel";

const number = (value, digits = 1) => Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: digits });

function ManagerDashboard() {
  const [batches, setBatches] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = async () => {
    setError("");
    try {
      const [inventoryResponse, assessmentResponse] = await Promise.all([getInventory(), getAssessments()]);
      setBatches(inventoryResponse.data);
      setAssessments(assessmentResponse.data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Waste sustainability details could not be loaded.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const assessmentByBatch = useMemo(
    () => new Map(assessments.map((assessment) => [assessment.batch_id, assessment])),
    [assessments],
  );

  return (
    <section className="space-y-6">
      <div className="overflow-hidden rounded-3xl bg-white shadow-xl ring-1 ring-slate-200">
        <div className="flex flex-col gap-3 border-b border-slate-100 p-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal-600">Waste Data Overview</p>
            <h2 className="mt-1 text-2xl font-black text-slate-950">Environmental impact by batch</h2>
            <p className="mt-1 text-sm text-slate-500">Read-only monitoring of registered waste and its calculated sustainability impact.</p>
          </div>
          <p className="rounded-full bg-teal-50 px-4 py-2 text-sm font-bold text-teal-700">{batches.length} total batches</p>
        </div>

        {error && <div className="m-5 flex items-center justify-between gap-3 rounded-2xl bg-rose-50 p-4 text-sm font-bold text-rose-700"><span>{error}</span><button type="button" onClick={loadData} className="rounded-xl bg-rose-700 px-3 py-2 text-white">Retry</button></div>}

        <div className="overflow-x-auto">
          <table className="min-w-[1050px] w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="p-4">Batch</th><th className="p-4">Fabric</th><th className="p-4">Quantity</th><th className="p-4">Status</th>
                <th className="p-4">CO₂ saved</th><th className="p-4">Water saved</th><th className="p-4">Diversion rate</th><th className="p-4">Landfill reduction</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {batches.map((batch) => {
                const assessment = assessmentByBatch.get(batch.waste_batch_id);
                const diversion = assessment?.quantity_kg ? assessment.landfill_reduction_kg / assessment.quantity_kg * 100 : null;
                return (
                  <tr key={batch.id} className="transition hover:bg-teal-50/50">
                    <td className="p-4 font-black text-slate-900">{batch.waste_batch_id}</td>
                    <td className="p-4">{batch.fabric_type}</td><td className="p-4">{batch.quantity}</td>
                    <td className="p-4"><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">{batch.status}</span></td>
                    <td className="p-4 font-semibold text-emerald-700">{assessment ? `${number(assessment.co2_saved_kg)} kg` : "Not assessed"}</td>
                    <td className="p-4 font-semibold text-cyan-700">{assessment ? `${number(assessment.water_saved_litres, 0)} L` : "Not assessed"}</td>
                    <td className="p-4 font-semibold text-teal-700">{diversion === null ? "Not assessed" : `${number(diversion)}%`}</td>
                    <td className="p-4 font-semibold text-lime-700">{assessment ? `${number(assessment.landfill_reduction_kg)} kg` : "Not assessed"}</td>
                  </tr>
                );
              })}
              {!loading && batches.length === 0 && <tr><td colSpan="8" className="p-10 text-center text-slate-500">No waste batches are available.</td></tr>}
              {loading && <tr><td colSpan="8" className="p-10 text-center font-semibold text-slate-500">Loading waste impact details...</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
      <ReportExportPanel
        title="Sustainability Officer Reports"
        description="Environmental, sustainability, ESG, and circularity reports available to the Sustainability Officer."
        reports={[
          { type: "sustainability", label: "Sustainability Report", description: "Sustainability metrics, waste diversion, carbon savings, and recovery performance." },
          { type: "environmental-impact", label: "Environmental Impact Report", description: "CO₂ savings, water savings, landfill reduction, and environmental scores." },
          { type: "circular-economy", label: "Circular Economy Report", description: "Circularity, reuse potential, material recovery, and recommended decisions." },
          { type: "esg", label: "ESG Report", description: "Waste, diversion, sustainability, and circularity performance for ESG reporting." },
        ]}
      />
    </section>
  );
}

export default ManagerDashboard;
