import { useAuth } from "../context/AuthContext";
import AdminDashboard from "./AdminDashboard";
import ManagerDashboard from "./ManagerDashboard";
import ManufacturerDashboard from "./ManufacturerDashboard";
import OperatorDashboard from "./OperatorDashboard";

const Dashboard = () => {
  const { user } = useAuth();

  if (!user) return <h2>Loading...</h2>;

  const role = user?.role || "operator";

  const dashboards = {
    admin: <AdminDashboard />,
    manager: <ManagerDashboard />,
    manufacturer: <ManufacturerDashboard />,
    operator: <OperatorDashboard />,
  };

  return (
    <div>
      <h1>Welcome, {user?.name}</h1>
      <p>Role: {role}</p>
      {dashboards[role] || dashboards.operator}
    </div>
  );
};

export default Dashboard;
