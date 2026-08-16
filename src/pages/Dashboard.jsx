import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import WasteBatchDetails from "../components/WasteBatchDetails";
import SustainabilityIntelligence from "../components/SustainabilityIntelligence";
import BrandLogo from "../components/BrandLogo";
import LoginIntro from "../components/LoginIntro";
import AdminDashboard from "./AdminDashboard";
import ManagerDashboard from "./ManagerDashboard";
import ManufacturerDashboard from "./ManufacturerDashboard";
import OperatorDashboard from "./OperatorDashboard";
import NotificationCenter from "../components/NotificationCenter";
import GlobalSearch from "../components/GlobalSearch";

const roleLabels = {
  admin: "Admin",
  manager: "Sustainability Officer",
  manufacturer: "Manufacturer",
  operator: "Recycling Facility",
};

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [showIntro, setShowIntro] = useState(() => sessionStorage.getItem("showLoginIntro") === "true");
  const finishIntro = useCallback(() => {
    sessionStorage.removeItem("showLoginIntro");
    setShowIntro(false);
  }, []);

  if (!user) return <h2 className="p-8 text-xl">Loading...</h2>;

  const role = user?.role || "operator";
  const dashboards = {
    admin: <AdminDashboard />,
    manager: <ManagerDashboard />,
    manufacturer: <ManufacturerDashboard />,
    operator: <OperatorDashboard />,
  };
  const roleNavigation = {
    admin: [["Overview", "#role-dashboard"], ["All Waste Details", "#waste-details"], ["Sustainability", "#sustainability-intelligence"], ["Model Insights", "/model-insights"], ["Training Feedback", "/training-feedback"]],
    manager: [["Sustainability", "#sustainability-intelligence"], ["Resource Conservation", "#resource-conservation"], ["Waste Overview", "#role-dashboard"], ["Circularity Decisions", "#circularity-decisions"]],
    manufacturer: [["Overview", "#role-dashboard"], ["Analyse & register", "/analyze"], ["Inventory", "/inventory"]],
    operator: [["Overview", "#role-dashboard"], ["Inventory", "/inventory"], ["Analyse textile", "/analyze"]],
  };

  return (
    <main className="dashboard-shell min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      {showIntro && <LoginIntro name={user?.name} onComplete={finishIntro} />}
      <div className="mx-auto max-w-7xl">
        <header className="dashboard-header mb-6 flex flex-col gap-4 rounded-3xl p-5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <BrandLogo compact />
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
          </div>
          <div className="flex w-full flex-wrap items-center gap-3 md:w-auto">
            <NotificationCenter user={user} />
            <button
              onClick={logout}
              className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-slate-300 transition hover:-translate-y-0.5 hover:bg-slate-800"
            >
              Logout
            </button>
          </div>
        </header>

        <nav aria-label="Dashboard navigation" className="mb-6 flex flex-wrap gap-2 rounded-2xl bg-white p-3 shadow-md ring-1 ring-slate-200">
          {(roleNavigation[role] || roleNavigation.operator).map(([label, destination]) => destination.startsWith("#") ? (
            <a key={label} href={destination} className="rounded-xl px-4 py-2 text-sm font-bold text-slate-700 transition hover:bg-cyan-50 hover:text-cyan-800">{label}</a>
          ) : (
            <Link key={label} to={destination} className="rounded-xl px-4 py-2 text-sm font-bold text-slate-700 transition hover:bg-cyan-50 hover:text-cyan-800">{label}</Link>
          ))}
          <div className="ml-auto w-full md:w-80"><GlobalSearch /></div>
        </nav>

        {role === "admin" && <div id="waste-details"><WasteBatchDetails /></div>}
        {role === "manager" && <div id="sustainability-intelligence"><SustainabilityIntelligence role={role} /></div>}
        <div id="role-dashboard" className={role === "admin" || role === "manager" ? "mt-6" : ""}>
          {dashboards[role] || dashboards.operator}
        </div>
        {role === "admin" && <div id="sustainability-intelligence"><SustainabilityIntelligence role={role} /></div>}
      </div>
    </main>
  );
};

export default Dashboard;
