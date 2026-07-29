import { useEffect, useMemo, useState } from "react";
import {
  downloadWasteItemReport,
  downloadWasteReport,
  getInventory,
} from "../services/inventoryService";

const statusStyles = {
  Pending: "bg-amber-100 text-amber-800",
  "Pickup Requested": "bg-orange-100 text-orange-800",
  Accepted: "bg-sky-100 text-sky-800",
  Collected: "bg-cyan-100 text-cyan-800",
  Processing: "bg-violet-100 text-violet-800",
  Recycled: "bg-emerald-100 text-emerald-800",
};

function WasteBatchDetails() {
  const [batches, setBatches] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [downloadingId, setDownloadingId] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    const loadBatches = async () => {
      try {
        const response = await getInventory();
        setBatches(response.data);
      } catch (requestError) {
        setError(requestError.response?.data?.detail || "Waste batch details could not be loaded.");
      } finally {
        setLoading(false);
      }
    };
    loadBatches();
  }, []);

  const filteredBatches = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return batches;
    return batches.filter((batch) =>
      [batch.waste_batch_id, batch.fabric_type, batch.quantity, batch.status].some((value) =>
        String(value || "").toLowerCase().includes(normalizedQuery),
      ),
    );
  }, [batches, query]);

  const downloadBatch = async (batch) => {
    setDownloadingId(batch.id);
    setError("");
    try {
      const response = await downloadWasteItemReport(batch.id);
      const url = URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${batch.waste_batch_id || `waste-${batch.id}`}-details.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "This waste batch PDF could not be downloaded.");
    } finally {
      setDownloadingId(null);
    }
  };

  const downloadAllBatches = async () => {
    setReportLoading(true);
    setError("");
    try {
      const response = await downloadWasteReport();
      const url = URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `textile-waste-report-${new Date().toISOString().slice(0, 10).replaceAll("-", "")}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "The waste PDF could not be downloaded.");
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <section className="mt-6 overflow-hidden rounded-3xl bg-white shadow-xl shadow-slate-200/60 ring-1 ring-slate-200">
      <div className="flex flex-col gap-4 bg-gradient-to-r from-slate-950 via-cyan-950 to-emerald-900 p-6 text-white sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-200">Waste records</p>
          <h2 className="mt-2 text-2xl font-black">
            {loading ? "Loading registered batches..." : `${batches.length} waste batches registered`}
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-slate-200">
            Review every uploaded batch and download an individual, neatly formatted PDF record.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            onClick={downloadAllBatches}
            disabled={reportLoading || loading || batches.length === 0}
            className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-black text-slate-950 shadow-lg transition hover:-translate-y-0.5 hover:bg-cyan-300 disabled:cursor-wait disabled:opacity-60"
          >
            {reportLoading ? "Preparing PDF..." : "Download Waste PDF"}
          </button>
          <button
            type="button"
            onClick={() => setIsOpen((current) => !current)}
            aria-expanded={isOpen}
            aria-controls="waste-batch-details"
            className="rounded-2xl bg-white px-5 py-3 text-sm font-black text-slate-950 shadow-lg transition hover:-translate-y-0.5 hover:bg-cyan-50"
          >
            {isOpen ? "Hide details" : "View details"}
          </button>
        </div>
      </div>

      {isOpen && (
        <div id="waste-batch-details" className="p-5 sm:p-6">
          {error && (
            <p role="alert" className="mb-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700">
              {error}
            </p>
          )}

          {!loading && batches.length > 0 && (
            <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="text-xl font-black text-slate-950">Waste batch details</h3>
                <p className="text-sm text-slate-500">Showing {filteredBatches.length} of {batches.length} records</p>
              </div>
              <label className="sm:w-80">
                <span className="sr-only">Search waste batches</span>
                <input
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search batch, fabric, quantity or status"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-cyan-500 focus:ring-4 focus:ring-cyan-100"
                />
              </label>
            </div>
          )}

          {loading && (
            <div className="grid gap-3" aria-label="Loading waste details">
              {[1, 2, 3].map((item) => <div key={item} className="h-14 animate-pulse rounded-2xl bg-slate-100" />)}
            </div>
          )}

          {!loading && !error && batches.length === 0 && (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <p className="font-black text-slate-800">No waste batches registered yet</p>
              <p className="mt-1 text-sm text-slate-500">New uploaded or manually registered batches will appear here.</p>
            </div>
          )}

          {!loading && batches.length > 0 && (
            <div className="overflow-x-auto rounded-2xl border border-slate-200">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
                  <tr>
                    <th scope="col" className="px-4 py-3">Batch no.</th>
                    <th scope="col" className="px-4 py-3">Fabric</th>
                    <th scope="col" className="px-4 py-3">Quantity</th>
                    <th scope="col" className="px-4 py-3">Status</th>
                    <th scope="col" className="px-4 py-3 text-right">PDF record</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {filteredBatches.map((batch) => (
                    <tr key={batch.id} className="transition hover:bg-cyan-50/50">
                      <td className="whitespace-nowrap px-4 py-4 font-black text-slate-900">{batch.waste_batch_id}</td>
                      <td className="px-4 py-4 text-slate-700">{batch.fabric_type}</td>
                      <td className="whitespace-nowrap px-4 py-4 text-slate-700">{batch.quantity}</td>
                      <td className="px-4 py-4">
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${statusStyles[batch.status] || "bg-slate-100 text-slate-700"}`}>
                          {batch.status}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right">
                        <button
                          type="button"
                          onClick={() => downloadBatch(batch)}
                          disabled={downloadingId === batch.id}
                          className="rounded-xl bg-slate-950 px-4 py-2 text-xs font-black text-white transition hover:bg-cyan-700 disabled:cursor-wait disabled:opacity-60"
                        >
                          {downloadingId === batch.id ? "Preparing..." : "Download PDF"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredBatches.length === 0 && (
                <p className="px-5 py-8 text-center text-sm text-slate-500">No batches match your search.</p>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default WasteBatchDetails;
