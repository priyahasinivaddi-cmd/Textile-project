import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { loginUser } from "../services/authService";

function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const { login } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    try {
      const response = await loginUser(form);
      login(response.data);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    }
  };

  return (
    <div className="form-container">
      <h2>Login</h2>
      {location.state?.message && (
        <p className="form-success">{location.state.message}</p>
      )}
      <form onSubmit={handleSubmit}>
        <input
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={(event) => setForm({ ...form, email: event.target.value })}
          required
        />
        <input
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={(event) =>
            setForm({ ...form, password: event.target.value })
          }
          required
        />
        {error && <p className="form-error">{error}</p>}
        <button type="submit">Login</button>
      </form>
      <p>
        New user? <Link to="/register">Register here</Link>
      </p>
    </div>
  );
}

export default Login;
