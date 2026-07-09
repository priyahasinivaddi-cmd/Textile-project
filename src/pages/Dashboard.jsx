import { useAuth } from "../context/AuthContext";
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

  if (!user) return <h2 className="p-8 text-xl">Loading...</h2>;

  const role = user?.role || "operator";
  const dashboards = {
    admin: <AdminDashboard />,
    manager: <ManagerDashboard />,
    manufacturer: <ManufacturerDashboard />,
    operator: <OperatorDashboard />,
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
          <button
            onClick={logout}
            className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-slate-300 transition hover:-translate-y-0.5 hover:bg-slate-800"
          >
            Logout
          </button>
        </header>

        {dashboards[role] || dashboards.operator}
      </div>
    </main>
  );
};

export default Dashboard;
