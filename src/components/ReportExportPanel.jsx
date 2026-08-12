import { useState } from "react";
import { downloadDedicatedReport } from "../services/sustainabilityService";

export default function ReportExportPanel({ reports, title = "Reports & Export", description }) {
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const download = async (type, format) => {
    const key = `${type}-${format}`;
    setBusy(key);
    setError("");
    try {
      const response = await downloadDedicatedReport(type, format);
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${type}-report.${format === "excel" ? "xlsx" : "pdf"}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "The report could not be downloaded.");
    } finally {
      setBusy("");
    }
  };

  return (
    <section className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
      <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal-600">Reports & Export System</p>
      <h2 className="mt-1 text-2xl font-black text-slate-950">{title}</h2>
      {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
      {error && <p className="mt-4 rounded-2xl bg-rose-50 p-3 text-sm font-bold text-rose-700">{error}</p>}
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {reports.map(({ type, label, description: reportDescription }) => (
          <article key={type} className="rounded-2xl bg-slate-50 p-4 ring-1 ring-slate-200">
            <h3 className="font-black text-slate-900">{label}</h3>
            <p className="mt-1 min-h-10 text-xs leading-5 text-slate-500">{reportDescription}</p>
            <div className="mt-4 flex gap-2">
              <button disabled={!!busy} onClick={() => download(type, "pdf")} className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white disabled:opacity-50">{busy === `${type}-pdf` ? "Preparing…" : "PDF export"}</button>
              <button disabled={!!busy} onClick={() => download(type, "excel")} className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white disabled:opacity-50">{busy === `${type}-excel` ? "Preparing…" : "Excel export"}</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
