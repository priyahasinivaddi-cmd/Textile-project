import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerUser } from "../services/authService";

function Register() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "operator",
  });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
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
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <section className="w-full max-w-2xl rounded-[2rem] bg-white p-8 shadow-2xl ring-1 ring-slate-200 sm:p-10">
        <p className="text-sm font-bold uppercase tracking-[0.22em] text-emerald-600">
          New user setup
        </p>
        <h1 className="mt-2 text-4xl font-black text-slate-950">Register</h1>
        <p className="mt-2 text-slate-500">
          Choose the correct role so the system opens the right dashboard after login.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
          <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          <select className="rounded-2xl border border-slate-200 px-4 py-3" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            <option value="manufacturer">Manufacturer</option>
            <option value="operator">Recycling Facility</option>
            <option value="manager">Sustainability Officer</option>
            <option value="admin">Admin</option>
          </select>
          {error && <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700">{error}</p>}
          <button className="rounded-2xl bg-gradient-to-r from-cyan-600 to-emerald-500 px-5 py-3 font-black text-white shadow-lg shadow-cyan-200">
            Register
          </button>
        </form>

        <p className="mt-5 text-sm text-slate-600">
          Already registered?{" "}
          <Link className="font-black text-cyan-700" to="/login">
            Login here
          </Link>
        </p>
      </section>
    </main>
  );
}

export default Register;
