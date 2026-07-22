import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { downloadWasteReport } from "../services/inventoryService";
import AdminDashboard from "./AdminDashboard";
import ManagerDashboard from "./ManagerDashboard";
import ManufacturerDashboard from "./ManufacturerDashboard";
import OperatorDashboard from "./OperatorDashboard";

const roleLabels = {
  admin: "Admin",
  manager: "Sustainability Officer",
  manufacturer: "Manufacturer",
  operator: "Recycling Facility",
};

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState("");

  if (!user) return <h2 className="p-8 text-xl">Loading...</h2>;

  const role = user?.role || "operator";
  const dashboards = {
    admin: <AdminDashboard />,
    manager: <ManagerDashboard />,
    manufacturer: <ManufacturerDashboard />,
    operator: <OperatorDashboard />,
  };

  const downloadReport = async () => {
    setReportLoading(true);
    setReportError("");
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
    } catch (error) {
      setReportError(error.response?.data?.detail || "The PDF report could not be downloaded.");
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-6 flex flex-col gap-4 rounded-3xl bg-white/85 p-5 shadow-xl shadow-slate-200/70 ring-1 ring-slate-200 backdrop-blur md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-cyan-600">
              Textile circularity platform
            </p>
            <h1 className="mt-2 text-3xl font-black text-slate-950 sm:text-4xl">
              Welcome, {user?.name}
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Role:{" "}
              <span className="font-semibold text-emerald-700">
                {roleLabels[role] || roleLabels.operator}
              </span>
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <button
              onClick={downloadReport}
              disabled={reportLoading}
              className="rounded-2xl bg-gradient-to-r from-cyan-600 to-emerald-500 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-cyan-200 transition hover:-translate-y-0.5 disabled:cursor-wait disabled:opacity-60"
            >
              {reportLoading ? "Preparing PDF..." : "Download Waste PDF"}
            </button>
            <button
              onClick={logout}
              className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-slate-300 transition hover:-translate-y-0.5 hover:bg-slate-800"
            >
              Logout
            </button>
          </div>
        </header>

        {reportError && (
          <p className="mb-5 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700 ring-1 ring-rose-100">
            {reportError}
          </p>
        )}

        {dashboards[role] || dashboards.operator}
      </div>
    </main>
  );
};

export default Dashboard;
