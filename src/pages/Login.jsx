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
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-[2rem] bg-white shadow-2xl ring-1 ring-slate-200 lg:grid-cols-[1fr_0.9fr]">
        <section className="bg-gradient-to-br from-cyan-600 via-emerald-500 to-lime-400 p-8 text-white sm:p-10">
          <p className="text-sm font-bold uppercase tracking-[0.24em] text-white/80">
            Textile Waste System
          </p>
          <h1 className="mt-6 text-4xl font-black leading-tight sm:text-5xl">
            Track waste from factory floor to recycled value.
          </h1>
          <div className="mt-8 grid gap-3 text-sm font-semibold sm:grid-cols-2">
            {["Manufacturer upload", "Recycling processing", "Impact analytics", "Admin control"].map((item) => (
              <div key={item} className="rounded-2xl bg-white/15 p-4 ring-1 ring-white/20">
                {item}
              </div>
            ))}
          </div>
        </section>

        <section className="p-8 sm:p-10">
          <h2 className="text-3xl font-black text-slate-950">Login</h2>
          <p className="mt-2 text-slate-500">
            Enter your account details to open your role dashboard.
          </p>
          {location.state?.message && (
            <p className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700">
              {location.state.message}
            </p>
          )}
          <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
            <input
              className="rounded-2xl border border-slate-200 px-4 py-3"
              placeholder="Email"
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              required
            />
            <input
              className="rounded-2xl border border-slate-200 px-4 py-3"
              placeholder="Password"
              type="password"
              value={form.password}
              onChange={(event) =>
                setForm({ ...form, password: event.target.value })
              }
              required
            />
            {error && <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700">{error}</p>}
            <button className="rounded-2xl bg-slate-950 px-5 py-3 font-black text-white shadow-lg shadow-slate-200 transition hover:-translate-y-0.5">
              Login
            </button>
          </form>
          <p className="mt-5 text-sm text-slate-600">
            New user?{" "}
            <Link className="font-black text-cyan-700" to="/register">
              Register here
            </Link>
          </p>
        </section>
      </div>
    </main>
  );
}

export default Login;
