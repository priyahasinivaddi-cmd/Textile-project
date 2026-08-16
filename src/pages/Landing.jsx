import { Link } from "react-router-dom";
import BrandLogo from "../components/BrandLogo";

const outcomes = [
  ["01", "Capture", "Register a textile batch and its source."],
  ["02", "Analyse", "Use one guided image workflow for material, condition and destination."],
  ["03", "Review", "Keep people in control of every AI-assisted decision."],
  ["04", "Recover", "Track reuse, recycling and measurable circular outcomes."],
];

export default function Landing() {
  return (
    <main className="min-h-screen overflow-hidden bg-slate-950 text-white">
      <div className="mx-auto max-w-7xl px-5 py-6 sm:px-8">
        <nav className="flex items-center justify-between" aria-label="Primary navigation">
          <BrandLogo compact />
          <div className="flex items-center gap-2">
            <Link to="/login" className="rounded-xl px-4 py-2 text-sm font-bold text-slate-200 hover:bg-white/10">Log in</Link>
            <Link to="/register" className="rounded-xl bg-emerald-400 px-4 py-2 text-sm font-black text-slate-950 hover:bg-emerald-300">Get started</Link>
          </div>
        </nav>

        <section className="grid min-h-[68vh] items-center gap-12 py-16 lg:grid-cols-[1.05fr_.95fr] lg:py-24">
          <div>
            <p className="text-sm font-black uppercase tracking-[.24em] text-emerald-300">Textile circularity, made operational</p>
            <h1 className="mt-5 max-w-3xl text-5xl font-black leading-[.98] tracking-tight sm:text-6xl lg:text-7xl">Turn textile waste into its next best use.</h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">One workspace to register waste, analyse material images, review AI-assisted recovery decisions and report circular impact.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/register" className="rounded-2xl bg-gradient-to-r from-cyan-400 to-emerald-400 px-6 py-3.5 font-black text-slate-950 shadow-xl shadow-emerald-950">Create an account</Link>
              <Link to="/login" className="rounded-2xl bg-white/10 px-6 py-3.5 font-bold ring-1 ring-white/20 hover:bg-white/15">Open your workspace</Link>
            </div>
            <p className="mt-5 text-sm text-slate-500">AI results are estimates and remain subject to human review.</p>
          </div>

          <div className="relative">
            <div className="absolute -inset-10 rounded-full bg-emerald-400/20 blur-3xl" />
            <div className="relative rounded-[2rem] bg-white/8 p-5 ring-1 ring-white/15 backdrop-blur-xl">
              <div className="rounded-3xl bg-gradient-to-br from-cyan-500 via-emerald-500 to-lime-400 p-7 text-slate-950">
                <p className="text-xs font-black uppercase tracking-[.2em]">Recovery decision</p>
                <p className="mt-3 text-4xl font-black">Recycle</p>
                <p className="mt-2 max-w-sm text-sm font-semibold text-slate-900/75">Cotton-rich woven textile · high recovery potential · reviewer confirmation required</p>
                <div className="mt-8 grid grid-cols-3 gap-2 text-center">
                  {[['82%', 'Confidence'], ['24 kg', 'Recoverable'], ['A', 'Quality']].map(([value, label]) => (
                    <div key={label} className="rounded-2xl bg-white/35 p-3"><p className="text-xl font-black">{value}</p><p className="text-xs font-bold opacity-70">{label}</p></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-3 border-t border-white/10 py-10 sm:grid-cols-2 lg:grid-cols-4" aria-label="How it works">
          {outcomes.map(([number, title, description]) => (
            <article key={number} className="rounded-2xl bg-white/5 p-5 ring-1 ring-white/10">
              <p className="text-xs font-black text-emerald-300">{number}</p><h2 className="mt-3 text-xl font-black">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
