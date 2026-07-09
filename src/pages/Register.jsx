import { useState } from "react";
import { registerUser } from "../services/authService";
import { Link, useNavigate } from "react-router-dom";

function Register() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "operator",
  });
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      await registerUser(form);
      navigate("/login", {
        state: { message: "Registration successful. Please login." },
      });
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    }
  };

  return (
    <div className="form-container">
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>
        <input
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <input
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <input
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        <select
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
        >
          <option value="operator">Recycling Operator</option>
          <option value="manager">Sustainability Manager</option>
          <option value="manufacturer">Manufacturer</option>
          <option value="admin">Admin</option>
        </select>
        {error && <p className="form-error">{error}</p>}
        <button type="submit">Register</button>
      </form>
      <p>
        Already registered? <Link to="/login">Login here</Link>
      </p>
    </div>
  );
}

export default Register;
