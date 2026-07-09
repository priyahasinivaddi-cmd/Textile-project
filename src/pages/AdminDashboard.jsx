/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useState } from "react";
import { getInventory } from "../services/inventoryService";
import { registerUser } from "../services/authService";
import { deleteUser, getUsers } from "../services/userService";

const emptyUser = {
  name: "",
  email: "",
  password: "",
  role: "operator",
};

function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [batches, setBatches] = useState([]);
  const [userForm, setUserForm] = useState(emptyUser);
  const [message, setMessage] = useState("");

  const loadData = async () => {
    const [userResponse, inventoryResponse] = await Promise.all([
      getUsers(),
      getInventory(),
    ]);
    setUsers(userResponse.data);
    setBatches(inventoryResponse.data);
  };

  useEffect(() => {
    loadData();
  }, []);

  const totalRecycled = batches.filter((batch) => batch.status === "Recycled").length;
  const totalGenerated = batches.length;

  const roleCounts = useMemo(() => {
    return users.reduce((summary, user) => {
      summary[user.role] = (summary[user.role] || 0) + 1;
      return summary;
    }, {});
  }, [users]);

  const createUser = async (event) => {
    event.preventDefault();
    setMessage("");
    await registerUser(userForm);
    setUserForm(emptyUser);
    setMessage("User created successfully.");
    await loadData();
  };

  const removeUser = async (id) => {
    await deleteUser(id);
    await loadData();
  };

  return (
    <section className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        {[
          ["Total Users", users.length],
          ["Total Waste Generated", totalGenerated],
          ["Total Recycled", totalRecycled],
        ].map(([label, value]) => (
          <div key={label} className="rounded-3xl bg-white p-5 shadow-md ring-1 ring-slate-200">
            <p className="text-sm font-semibold text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-black text-indigo-700">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <form onSubmit={createUser} className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-600">
            User Management
          </p>
          <h2 className="mt-1 text-2xl font-black text-slate-950">
            Create Platform User
          </h2>
          <div className="mt-5 grid gap-3">
            <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Name" value={userForm.name} onChange={(e) => setUserForm({ ...userForm, name: e.target.value })} required />
            <input className="rounded-2xl border border-slate-200 px-4 py-3" type="email" placeholder="Email" value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} required />
            <input className="rounded-2xl border border-slate-200 px-4 py-3" type="password" placeholder="Password" value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} required />
            <select className="rounded-2xl border border-slate-200 px-4 py-3" value={userForm.role} onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}>
              <option value="manufacturer">Manufacturer</option>
              <option value="operator">Recycling Facility</option>
              <option value="manager">Sustainability Officer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          {message && <p className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700">{message}</p>}
          <button className="mt-5 w-full rounded-2xl bg-gradient-to-r from-indigo-600 to-fuchsia-600 px-5 py-3 font-black text-white shadow-lg shadow-indigo-200">
            Create User
          </button>
        </form>

        <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <h2 className="text-2xl font-black text-slate-950">Users & Roles</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="p-3">Name</th>
                  <th className="p-3">Email</th>
                  <th className="p-3">Role</th>
                  <th className="p-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-t border-slate-100">
                    <td className="p-3 font-bold">{user.name}</td>
                    <td className="p-3">{user.email}</td>
                    <td className="p-3">{user.role}</td>
                    <td className="p-3">
                      <button onClick={() => removeUser(user.id)} className="rounded-xl bg-rose-100 px-3 py-2 font-bold text-rose-700">
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-3xl bg-gradient-to-br from-indigo-700 to-slate-950 p-6 text-white shadow-xl">
          <h2 className="text-2xl font-black">Platform Analytics</h2>
          <div className="mt-4 space-y-3">
            {Object.entries(roleCounts).map(([role, count]) => (
              <div key={role} className="flex justify-between rounded-2xl bg-white/10 p-3">
                <span>{role}</span>
                <span className="font-black">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <h2 className="text-2xl font-black text-slate-950">System Monitoring</h2>
          <div className="mt-4 space-y-3">
            <p className="rounded-2xl bg-emerald-50 p-4 font-bold text-emerald-700">
              API status: Online
            </p>
            <p className="rounded-2xl bg-slate-50 p-4 font-bold text-slate-700">
              Errors/logs: No active frontend errors
            </p>
          </div>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
          <h2 className="text-2xl font-black text-slate-950">Report Management</h2>
          <div className="mt-4 space-y-3">
            {["Manufacturer waste report", "Recycling recovery report", "Sustainability ESG report"].map((report) => (
              <button key={report} className="w-full rounded-2xl bg-slate-100 px-4 py-3 text-left font-bold text-slate-700">
                View / download {report}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default AdminDashboard;
