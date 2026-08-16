import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { downloadWasteCsv, downloadWasteItemReport, downloadWasteReport, getInventory } from "../services/inventoryService";

const statusStyles = {
  pending: "bg-amber-50 text-amber-700 ring-amber-200",
  processing: "bg-cyan-50 text-cyan-700 ring-cyan-200",
  processed: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  rejected: "bg-rose-50 text-rose-700 ring-rose-200",
};

const normalize = (value) => String(value || "").toLowerCase();

function Inventory() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [downloadingId, setDownloadingId] = useState(null);
  const [downloadError, setDownloadError] = useState("");
  const [selectedItem, setSelectedItem] = useState(null);
  const [exporting, setExporting] = useState("");

  useEffect(() => {
    const loadInventory = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await getInventory();
        setData(response.data);
      } catch (requestError) {
        setError(requestError.response?.data?.detail || "Inventory could not be loaded. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    loadInventory();
  }, []);

  const statuses = useMemo(
    () => [...new Set(data.map((item) => item.status).filter(Boolean))].sort((a, b) => a.localeCompare(b)),
    [data],
  );

  const filteredData = useMemo(() => {
    const query = normalize(search).trim();
    return data.filter((item) => {
      const matchesStatus = statusFilter === "all" || item.status === statusFilter;
      const matchesSearch = !query || [
        item.waste_batch_id,
        item.fabric_type,
        item.source,
        item.quantity,
        item.condition,
        item.uploaded_by,
      ].some((value) => normalize(value).includes(query));
      return matchesStatus && matchesSearch;
    });
  }, [data, search, statusFilter]);

  const downloadItemPdf = async (item) => {
    setDownloadingId(item.id);
    setDownloadError("");
    try {
      const response = await downloadWasteItemReport(item.id);
      const url = URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${item.waste_batch_id || `waste-${item.id}`}-report.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setDownloadError(
        requestError.response?.data?.detail ||
          `The PDF for ${item.waste_batch_id} could not be downloaded.`,
      );
    } finally {
      setDownloadingId(null);
    }
  };

  const exportAll = async (format) => {
    setExporting(format);
    setDownloadError("");
    try {
      const response = format === "csv" ? await downloadWasteCsv() : await downloadWasteReport();
      const url = URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `textile-waste-batches.${format}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setDownloadError(requestError.response?.data?.detail || "The waste-batch export could not be downloaded.");
    } finally { setExporting(""); }
  };

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-6 flex flex-col gap-4 rounded-3xl bg-slate-950 p-6 text-white shadow-xl md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-cyan-300">Textile circularity platform</p>
            <h1 className="mt-2 text-3xl font-black sm:text-4xl">Waste inventory</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">
              Review every registered batch and download its complete information as an individual PDF.
            </p>
          </div>
          <nav className="flex flex-wrap gap-2" aria-label="Inventory navigation">
            <Link to="/dashboard" className="rounded-xl bg-white/10 px-4 py-2.5 text-sm font-bold ring-1 ring-white/20 transition hover:bg-white/20">
              Dashboard
            </Link>
            <Link to="/upload" className="rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 px-4 py-2.5 text-sm font-black shadow-lg">
              + Register waste
            </Link>
            <button type="button" onClick={() => exportAll("csv")} disabled={!!exporting} className="rounded-xl bg-white/10 px-4 py-2.5 text-sm font-bold ring-1 ring-white/20 disabled:opacity-60">{exporting === "csv" ? "Exporting…" : "Export all CSV"}</button>
            <button type="button" onClick={() => exportAll("pdf")} disabled={!!exporting} className="rounded-xl bg-white/10 px-4 py-2.5 text-sm font-bold ring-1 ring-white/20 disabled:opacity-60">{exporting === "pdf" ? "Exporting…" : "Export all PDF"}</button>
          </nav>
        </header>

        <section className="rounded-3xl bg-white p-5 shadow-xl ring-1 ring-slate-200 sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-2xl font-black text-slate-950">Registered waste</h2>
              <p className="mt-1 text-sm text-slate-500">Showing {filteredData.length} of {data.length} batches</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-[minmax(240px,1fr)_180px]">
              <label className="grid gap-1 text-xs font-bold text-slate-600">
                Search inventory
                <input
                  className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-normal outline-none transition focus:border-cyan-500 focus:ring-4 focus:ring-cyan-100"
                  type="search"
                  placeholder="Batch, fabric, source..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>
              <label className="grid gap-1 text-xs font-bold text-slate-600">
                Status
                <select
                  className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-normal outline-none focus:border-cyan-500"
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                >
                  <option value="all">All statuses</option>
                  {statuses.map((status) => <option key={status} value={status}>{status}</option>)}
                </select>
              </label>
            </div>
          </div>

          {downloadError && (
            <p role="alert" className="mt-5 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700 ring-1 ring-rose-100">
              {downloadError}
            </p>
          )}

          {loading ? (
            <div className="mt-6 grid gap-3" aria-label="Loading inventory">
              {[1, 2, 3].map((item) => <div key={item} className="h-16 animate-pulse rounded-2xl bg-slate-100" />)}
            </div>
          ) : error ? (
            <div className="mt-6 rounded-2xl bg-rose-50 p-6 text-center ring-1 ring-rose-100">
              <p className="font-bold text-rose-700">{error}</p>
            </div>
          ) : filteredData.length === 0 ? (
            <div className="mt-6 rounded-2xl bg-slate-50 p-10 text-center ring-1 ring-slate-100">
              <p className="text-lg font-black text-slate-800">{data.length ? "No batches match these filters" : "No waste registered yet"}</p>
              <p className="mt-1 text-sm text-slate-500">
                {data.length ? "Try changing the search term or status." : "Register your first waste batch to see it here."}
              </p>
              {!data.length && <Link to="/analyze" className="mt-5 inline-flex rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-black text-white">Analyse and register a batch</Link>}
            </div>
          ) : (
            <div className="mt-6 overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500">
                    <th className="px-3 py-3">Batch information</th>
                    <th className="px-3 py-3">Source</th>
                    <th className="px-3 py-3">Quantity</th>
                    <th className="px-3 py-3">Collected</th>
                    <th className="px-3 py-3">Uploaded by</th>
                    <th className="px-3 py-3">Status</th>
                    <th className="px-3 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((item) => {
                    const style = statusStyles[normalize(item.status)] || "bg-slate-100 text-slate-700 ring-slate-200";
                    return (
                      <tr key={item.id} className="border-b border-slate-100 align-middle transition hover:bg-slate-50">
                        <td className="px-3 py-4">
                          <p className="font-black text-slate-950">{item.waste_batch_id}</p>
                          <p className="mt-1 text-xs text-slate-500">
                            {item.fabric_type} · {item.color || "Color not recorded"} · {item.condition}
                          </p>
                        </td>
                        <td className="px-3 py-4 text-slate-700">{item.source}</td>
                        <td className="px-3 py-4 font-bold text-slate-800">{item.quantity}</td>
                        <td className="px-3 py-4 text-slate-600">{item.collection_date || "Not provided"}</td>
                        <td className="px-3 py-4 font-semibold text-slate-700">{item.uploaded_by || "Unknown user"}</td>
                        <td className="px-3 py-4">
                          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-black ring-1 ${style}`}>
                            {item.status || "Unspecified"}
                          </span>
                        </td>
                        <td className="px-3 py-4 text-right">
                          <button type="button" onClick={() => setSelectedItem(item)} className="mr-2 rounded-xl bg-cyan-50 px-4 py-2.5 text-xs font-black text-cyan-800 ring-1 ring-cyan-100">View</button>
                          <button
                            type="button"
                            disabled={downloadingId === item.id}
                            onClick={() => downloadItemPdf(item)}
                            className="whitespace-nowrap rounded-xl bg-slate-950 px-4 py-2.5 text-xs font-black text-white shadow-md transition hover:-translate-y-0.5 hover:bg-cyan-700 disabled:cursor-wait disabled:opacity-60"
                            aria-label={`Download PDF report for ${item.waste_batch_id}`}
                          >
                            {downloadingId === item.id ? "Preparing..." : "Download PDF"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/45 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="batch-detail-title" onMouseDown={event => { if (event.target === event.currentTarget) setSelectedItem(null); }}>
          <aside className="h-full w-full max-w-lg overflow-y-auto bg-white p-6 shadow-2xl sm:p-8">
            <div className="flex items-start justify-between gap-4">
              <div><p className="text-xs font-black uppercase tracking-wider text-cyan-700">Batch detail</p><h2 id="batch-detail-title" className="mt-1 text-3xl font-black text-slate-950">{selectedItem.waste_batch_id}</h2></div>
              <button type="button" onClick={() => setSelectedItem(null)} aria-label="Close batch details" className="rounded-full bg-slate-100 px-3 py-2 font-black text-slate-700">×</button>
            </div>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {[["Fabric", selectedItem.fabric_type], ["Quantity", selectedItem.quantity], ["Source", selectedItem.source], ["Condition", selectedItem.condition], ["Colour", selectedItem.color || "Not recorded"], ["Collected", selectedItem.collection_date || "Not provided"], ["Uploaded by", selectedItem.uploaded_by || "Unknown user"], ["Status", selectedItem.status || "Unspecified"], ["Assigned to", selectedItem.assigned_to || "Not assigned"]].map(([label, value]) => (
                <div key={label} className="rounded-2xl bg-slate-50 p-4 ring-1 ring-slate-100"><p className="text-xs font-bold uppercase tracking-wider text-slate-500">{label}</p><p className="mt-1 font-black text-slate-900">{value}</p></div>
              ))}
            </div>
            <div className="mt-6 rounded-2xl bg-amber-50 p-4 text-sm text-amber-900 ring-1 ring-amber-100"><strong>AI-assisted record.</strong> Material and recovery recommendations are estimates and should be confirmed by a reviewer.</div>
            <button type="button" onClick={() => downloadItemPdf(selectedItem)} disabled={downloadingId === selectedItem.id} className="mt-6 w-full rounded-xl bg-slate-950 px-4 py-3 font-black text-white disabled:opacity-60">{downloadingId === selectedItem.id ? "Preparing…" : "Download complete PDF"}</button>
          </aside>
        </div>
      )}
    </main>
  );
}

export default Inventory;
