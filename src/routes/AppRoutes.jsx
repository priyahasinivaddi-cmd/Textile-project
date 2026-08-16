import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "../pages/Login";
import Register from "../pages/Register";
import Dashboard from "../pages/Dashboard";
import Inventory from "../pages/Inventory";
import WasteAnalysis from "../pages/WasteAnalysis";
import ModelInsights from "../pages/ModelInsights";
import TrainingFeedback from "../pages/TrainingFeedback";
import Landing from "../pages/Landing";
import { useAuth } from "../context/AuthContext";

const PrivateRoute = ({ children }) => {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
};

function AppRoutes() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />

        <Route path="/login" element={<Login />} />

        <Route path="/register" element={<Register />} />

        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          }
        />

        <Route
          path="/inventory"
          element={
            <PrivateRoute>
              <Inventory />
            </PrivateRoute>
          }
        />

        <Route path="/upload" element={<Navigate to="/analyze" replace />} />

        {/* Public standalone analysis page — no auth required */}
        <Route path="/analyze" element={<PrivateRoute><WasteAnalysis /></PrivateRoute>} />

        <Route path="/composition-prediction" element={<Navigate to="/analyze" replace />} />
        <Route path="/model-insights" element={<PrivateRoute><ModelInsights /></PrivateRoute>} />
        <Route path="/training-feedback" element={<PrivateRoute><TrainingFeedback /></PrivateRoute>} />
      </Routes>
    </Router>
  );
}

export default AppRoutes;
