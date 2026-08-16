import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { globalSearch } from "../services/platformService";

export default function GlobalSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const request = useRef(0);
  useEffect(() => {
    if (query.trim().length < 2) return;
    const current = ++request.current;
    const timer = window.setTimeout(async () => {
      try { const { data } = await globalSearch(query.trim()); if (current === request.current) { setResults(data.results); setOpen(true); } } catch { if (current === request.current) setResults([]); }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [query]);
  return <div className="relative min-w-0 flex-1 sm:max-w-sm">
    <label htmlFor="global-search" className="sr-only">Search garments and analyses</label>
    <input id="global-search" type="search" value={query} onFocus={() => setOpen(true)} onChange={event => setQuery(event.target.value)} placeholder="Search garments, materials, destinations…" className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-200" />
    {open && query.length >= 2 && <div className="absolute right-0 z-50 mt-2 max-h-80 w-full min-w-[290px] overflow-auto rounded-2xl bg-white p-2 shadow-2xl ring-1 ring-slate-200">
      {results.map(item => <Link key={`${item.kind}-${item.id}`} to={item.url} onClick={() => setOpen(false)} className="block rounded-xl px-3 py-2 hover:bg-cyan-50"><span className="block text-sm font-black text-slate-900">{item.title}</span><span className="block text-xs text-slate-500">{item.kind} · {item.subtitle}</span></Link>)}
      {!results.length && <p className="p-4 text-center text-sm text-slate-500">No matching garments or analyses.</p>}
    </div>}
  </div>;
}
