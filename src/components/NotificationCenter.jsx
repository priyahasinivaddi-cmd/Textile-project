/* eslint-disable react-hooks/set-state-in-effect */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createAnnouncement, getNotifications, removeAnnouncement } from "../services/notificationService";

const tones = {
  info: "bg-cyan-50 text-cyan-800 ring-cyan-200",
  success: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  warning: "bg-amber-50 text-amber-900 ring-amber-200",
  danger: "bg-rose-50 text-rose-800 ring-rose-200",
};

const categoryLabels = { collection: "Collection", opportunity: "Opportunity", milestone: "Milestone", inventory: "Inventory", announcement: "Announcement" };

export default function NotificationCenter({ user }) {
  const storageKey = `readNotifications:${user?.email || user?.name || "user"}`;
  const [notifications, setNotifications] = useState([]);
  const [readIds, setReadIds] = useState(() => new Set(JSON.parse(localStorage.getItem(storageKey) || "[]")));
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");
  const [form, setForm] = useState({ title: "", message: "", severity: "info", audience: "all" });

  const load = useCallback(async () => {
    try {
      const response = await getNotifications();
      setNotifications(response.data);
      setError("");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Notifications could not be loaded.");
    }
  }, []);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 60000);
    return () => window.clearInterval(timer);
  }, [load]);

  const unread = notifications.filter((item) => !readIds.has(item.id)).length;
  const visible = useMemo(() => filter === "all" ? notifications : notifications.filter((item) => item.category === filter), [filter, notifications]);

  const saveRead = (next) => {
    setReadIds(next);
    localStorage.setItem(storageKey, JSON.stringify([...next]));
  };
  const markRead = (id) => saveRead(new Set([...readIds, id]));
  const markAllRead = () => saveRead(new Set(notifications.map((item) => item.id)));

  const publish = async (event) => {
    event.preventDefault();
    try {
      await createAnnouncement(form);
      setForm({ title: "", message: "", severity: "info", audience: "all" });
      await load();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Announcement could not be published.");
    }
  };

  const deactivate = async (id) => {
    await removeAnnouncement(String(id).replace("announcement-", ""));
    await load();
  };

  return (
    <div className="relative">
      <button type="button" onClick={() => setOpen(!open)} aria-label={`${unread} unread notifications`} className="relative rounded-2xl bg-white px-4 py-3 text-sm font-black text-slate-800 shadow-md ring-1 ring-slate-200">
        Notifications
        {unread > 0 && <span className="absolute -right-2 -top-2 min-w-6 rounded-full bg-rose-600 px-1.5 py-1 text-xs text-white">{unread > 99 ? "99+" : unread}</span>}
      </button>
      {open && <div className="absolute right-0 z-50 mt-3 max-h-[75vh] w-[min(92vw,620px)] overflow-y-auto rounded-3xl bg-white p-5 text-left shadow-2xl ring-1 ring-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-teal-600">Notification & Alert System</p><h2 className="text-xl font-black text-slate-950">Alerts and announcements</h2></div><button onClick={markAllRead} className="text-xs font-bold text-cyan-700">Mark all read</button></div>
        <div className="mt-4 flex flex-wrap gap-2">{["all", "collection", "opportunity", "milestone", "inventory", "announcement"].map((item) => <button key={item} onClick={() => setFilter(item)} className={`rounded-full px-3 py-1.5 text-xs font-bold ${filter === item ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}>{item === "all" ? "All" : categoryLabels[item]}</button>)}</div>
        {error && <p className="mt-4 rounded-xl bg-rose-50 p-3 text-sm font-bold text-rose-700">{error}</p>}
        <div className="mt-4 space-y-3">{visible.map((item) => <article key={item.id} onClick={() => markRead(item.id)} className={`rounded-2xl p-4 ring-1 ${tones[item.severity] || tones.info} ${readIds.has(item.id) ? "opacity-65" : ""}`}><div className="flex items-start justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-wider">{categoryLabels[item.category]}</p><h3 className="mt-1 font-black">{item.title}</h3></div>{!readIds.has(item.id) && <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-current" />}</div><p className="mt-2 text-sm leading-5">{item.message}</p><div className="mt-3 flex gap-3">{item.action_url && <Link to={item.action_url} onClick={() => setOpen(false)} className="text-xs font-black underline">Open related page</Link>}{user.role === "admin" && item.category === "announcement" && <button onClick={(event) => { event.stopPropagation(); deactivate(item.id); }} className="text-xs font-black underline">Deactivate</button>}</div></article>)}{!visible.length && <p className="rounded-2xl bg-slate-50 p-6 text-center text-sm text-slate-500">No alerts in this category.</p>}</div>
        {user.role === "admin" && <form onSubmit={publish} className="mt-5 rounded-2xl bg-slate-950 p-4 text-white"><h3 className="font-black">Publish platform announcement</h3><div className="mt-3 grid gap-2"><input required maxLength="120" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Announcement title" className="rounded-xl bg-white px-3 py-2 text-sm text-slate-900"/><textarea required maxLength="1000" value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} placeholder="Message" rows="3" className="rounded-xl bg-white px-3 py-2 text-sm text-slate-900"/><div className="grid grid-cols-2 gap-2"><select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })} className="rounded-xl bg-white px-3 py-2 text-sm text-slate-900"><option value="info">Information</option><option value="success">Success</option><option value="warning">Warning</option><option value="danger">Urgent</option></select><select value={form.audience} onChange={(e) => setForm({ ...form, audience: e.target.value })} className="rounded-xl bg-white px-3 py-2 text-sm text-slate-900"><option value="all">Everyone</option><option value="manager">Sustainability Officers</option><option value="operator">Recycling Facilities</option><option value="manufacturer">Manufacturers</option><option value="admin">Admins</option></select></div><button className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-black text-slate-950">Publish announcement</button></div></form>}
      </div>}
    </div>
  );
}
