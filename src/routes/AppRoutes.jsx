import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "../pages/Login";
import Register from "../pages/Register";
import Dashboard from "../pages/Dashboard";
import Inventory from "../pages/Inventory";
import UploadWaste from "../pages/UploadWaste";
import { useAuth } from "../context/AuthContext";

const PrivateRoute = ({ children }) => {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
};

function AppRoutes() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />

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

        <Route
          path="/upload"
          element={
            <PrivateRoute>
              <UploadWaste />
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default AppRoutes;
