import { useState, useRef, useCallback } from "react";
import { Link } from "react-router-dom";
import { analyzeImage } from "../services/pipelineService";

// ─── Pipeline step definitions ─────────────────────────────────────────────
const PIPELINE_STEPS = [
  { id: "upload",   label: "Image Upload",        desc: "Validating & persisting image" },
  { id: "extract",  label: "Feature Extraction",  desc: "Analysing pixel statistics" },
  { id: "material", label: "Material Detection",  desc: "Classifying fabric type & blend" },
  { id: "waste",    label: "Waste Classification",desc: "Grading condition & disposal route" },
  { id: "recs",     label: "Recommendations",     desc: "Generating circular economy actions" },
];

// ─── Category badge colours (Tailwind safe-listed via full string) ──────────
const CATEGORY_BADGE = {
  Reusable:    "bg-emerald-100 text-emerald-800 border-emerald-300",
  Repairable:  "bg-sky-100 text-sky-800 border-sky-300",
  Upcyclable:  "bg-violet-100 text-violet-800 border-violet-300",
  Recyclable:  "bg-cyan-100 text-cyan-800 border-cyan-300",
  Compostable: "bg-lime-100 text-lime-800 border-lime-300",
  Hazardous:   "bg-rose-100 text-rose-800 border-rose-300",
};
const CATEGORY_ICON = {
  Reusable: "♻️", Repairable: "🔧", Upcyclable: "🎨",
  Recyclable: "🔄", Compostable: "🌱", Hazardous: "⚠️",
};
const QUALITY_BADGE = {
  high:   "bg-emerald-50 text-emerald-700 border-emerald-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200",
  low:    "bg-rose-50 text-rose-700 border-rose-200",
};
const REUSE_COLOR = { High: "text-emerald-600", Medium: "text-amber-500", Low: "text-rose-500" };

// ─── Tiny helper components ─────────────────────────────────────────────────
function StepRow({ step, index }) {
  const s = step.status;
  const circle =
    s === "success" ? "border-emerald-500 bg-emerald-50 text-emerald-600" :
    s === "loading" ? "border-cyan-500 bg-cyan-50 text-cyan-600 animate-pulse" :
    s === "error"   ? "border-rose-500 bg-rose-50 text-rose-600" :
                      "border-slate-200 bg-slate-50 text-slate-400";
  const badge =
    s === "success" ? "bg-emerald-100 text-emerald-700" :
    s === "loading" ? "bg-cyan-100 text-cyan-700" :
    s === "error"   ? "bg-rose-100 text-rose-700" :
                      "bg-slate-100 text-slate-400";

  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-slate-50/50 px-4 py-3">
      <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-black ${circle}`}>
        {s === "success" ? "✓" : s === "error" ? "✕" : index + 1}
      </div>
      <div className="flex-1 text-left">
        <p className={`text-sm font-bold ${s === "loading" ? "text-cyan-700" : "text-slate-700"}`}>
          {step.label}
        </p>
        {s === "loading" && (
          <p className="text-xs text-slate-400">{PIPELINE_STEPS[index].desc}</p>
        )}
      </div>
      <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${badge}`}>
        {s === "idle" ? "Queued" : s === "loading" ? "Running" : s === "success" ? "Done" : "Failed"}
      </span>
    </div>
  );
}

// ─── Main page ──────────────────────────────────────────────────────────────
export default function WasteAnalysis() {
  const [file, setFile]         = useState(null);
  const [preview, setPreview]   = useState(null);
  const [sensitivity, setSens]  = useState(50);
  const [isDragging, setDrag]   = useState(false);

  const [steps, setSteps]       = useState(() => PIPELINE_STEPS.map(s => ({ ...s, status: "idle" })));
  const [running, setRunning]   = useState(false);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState("");
  const [activeTab, setTab]     = useState("features");

  const fileRef    = useRef(null);
  const resultsRef = useRef(null);

  const applyFile = (f) => {
    if (!f || !f.type.startsWith("image/")) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError("");
    setSteps(PIPELINE_STEPS.map(s => ({ ...s, status: "idle" })));
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault(); setDrag(false);
    applyFile(e.dataTransfer.files?.[0]);
  }, []);

  const clearAll = () => {
    setFile(null); setPreview(null); setResult(null); setError("");
    setSteps(PIPELINE_STEPS.map(s => ({ ...s, status: "idle" })));
  };

  const updateStep = (i, status) =>
    setSteps(prev => prev.map((s, idx) => idx === i ? { ...s, status } : s));

  const delay = ms => new Promise(r => setTimeout(r, ms));

  const runPipeline = async () => {
    if (!file || running) return;
    setRunning(true); setError(""); setResult(null);
    setSteps(PIPELINE_STEPS.map(s => ({ ...s, status: "idle" })));
    try {
      updateStep(0, "loading"); await delay(600); updateStep(0, "success");
      updateStep(1, "loading");
      const { data } = await analyzeImage(file, sensitivity / 100);
      await delay(400); updateStep(1, "success");
      updateStep(2, "loading"); await delay(700); updateStep(2, "success");
      updateStep(3, "loading"); await delay(600); updateStep(3, "success");
      updateStep(4, "loading"); await delay(500); updateStep(4, "success");
      setResult(data); setTab("features");
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 200);
    } catch (err) {
      const msg = err?.response?.data?.detail || "Pipeline failed. Please try another image.";
      setError(msg);
      setSteps(prev => prev.map(s => s.status === "loading" ? { ...s, status: "error" } : s));
    } finally {
      setRunning(false);
    }
  };

  const catBadge = result ? (CATEGORY_BADGE[result.waste_classification?.category] || CATEGORY_BADGE.Recyclable) : "";
  const catIcon  = result ? (CATEGORY_ICON[result.waste_classification?.category]  || "🔄") : "";

  // ── Image URL from backend (/static/uploads/...)
  const imageUrl = result
    ? `http://127.0.0.1:8000${result.image_url}`
    : null;

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">

        {/* ── Header ── */}
        <header className="mb-8 flex flex-col gap-4 rounded-3xl bg-white/5 p-6 shadow-xl ring-1 ring-white/10 backdrop-blur-md md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-cyan-400">
              AI Circular Intelligence Pipeline
            </p>
            <h1 className="mt-2 text-3xl font-black text-white sm:text-4xl">
              Textile Waste Intelligence
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Upload a textile image — extract features, classify material &amp; waste, get recycling actions.
            </p>
          </div>
          <Link
            to="/dashboard"
            className="self-start rounded-2xl bg-white/10 px-5 py-3 text-sm font-bold text-white ring-1 ring-white/20 transition hover:bg-white/20"
          >
            ← Back to Dashboard
          </Link>
        </header>

        {/* ── Tags ── */}
        <div className="mb-8 flex flex-wrap gap-2">
          {["Color Detection","Texture Analysis","Pattern Recognition","Damage Scanning","Material Classification","Waste Grading","Recycling Recommendations"].map(t => (
            <span key={t} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-slate-400">
              {t}
            </span>
          ))}
        </div>

        <div className="grid gap-8 lg:grid-cols-12">

          {/* ── LEFT COLUMN ── */}
          <div className="space-y-6 lg:col-span-5">

            {/* Upload card */}
            <div className="rounded-3xl bg-white/5 p-6 ring-1 ring-white/10 backdrop-blur-md">
              <h2 className="mb-4 text-lg font-black text-white">Upload Textile Image</h2>

              {!preview ? (
                <div
                  onDragOver={e => { e.preventDefault(); setDrag(true); }}
                  onDragLeave={() => setDrag(false)}
                  onDrop={handleDrop}
                  onClick={() => fileRef.current?.click()}
                  className={`group flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 text-center transition ${
                    isDragging
                      ? "border-cyan-400 bg-cyan-400/10"
                      : "border-white/20 bg-white/3 hover:border-cyan-400 hover:bg-cyan-400/5"
                  }`}
                >
                  <input ref={fileRef} type="file" accept="image/*" className="hidden"
                    onChange={e => applyFile(e.target.files?.[0])} />
                  <div className="mb-4 rounded-full bg-cyan-400/15 p-4 text-cyan-400 transition group-hover:scale-110">
                    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                  </div>
                  <p className="text-base font-bold text-white">Drag &amp; drop textile image</p>
                  <p className="mt-2 text-xs text-slate-400">PNG, JPG, JPEG · Optimal 800×800 px</p>
                  <button type="button"
                    className="mt-4 rounded-xl bg-cyan-500 px-4 py-2 text-xs font-bold text-white transition hover:bg-cyan-400">
                    Browse Files
                  </button>
                </div>
              ) : (
                <div className="relative overflow-hidden rounded-2xl">
                  <img src={preview} alt="Textile preview" className="h-56 w-full object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between">
                    <span className="truncate text-xs font-semibold text-white">{file?.name}</span>
                    <button onClick={clearAll} disabled={running}
                      className="rounded-full bg-white/20 px-3 py-1 text-xs font-bold text-white backdrop-blur hover:bg-white/30">
                      ✕ Clear
                    </button>
                  </div>
                </div>
              )}

              {/* Sensitivity slider */}
              <div className="mt-6 border-t border-white/10 pt-5">
                <div className="mb-2 flex items-center justify-between">
                  <label className="text-sm font-bold text-slate-300">AI Defect Sensitivity</label>
                  <span className="rounded-full bg-cyan-400/15 px-2.5 py-0.5 text-xs font-black text-cyan-400">{sensitivity}%</span>
                </div>
                <input type="range" min={0} max={100} value={sensitivity}
                  onChange={e => setSens(Number(e.target.value))} disabled={running}
                  className="h-2 w-full cursor-pointer appearance-none rounded-full bg-white/15 accent-cyan-400" />
                <p className="mt-1.5 text-xs text-slate-500">
                  Higher values flag micro-tears and faint stains more aggressively.
                </p>
              </div>

              {/* Run button */}
              <button
                id="run-pipeline-btn"
                onClick={runPipeline}
                disabled={!file || running}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500 to-emerald-500 py-3.5 text-sm font-black text-white shadow-lg shadow-cyan-500/20 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:from-slate-600 disabled:to-slate-700 disabled:shadow-none"
              >
                {running ? (
                  <>
                    <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeOpacity="0.25" />
                      <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Processing Pipeline…
                  </>
                ) : (
                  <>
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Run Analysis Pipeline
                  </>
                )}
              </button>
            </div>

            {/* Pipeline steps */}
            {steps.some(s => s.status !== "idle") && (
              <div className="rounded-3xl bg-white/5 p-6 ring-1 ring-white/10 backdrop-blur-md">
                <h3 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-400">Pipeline Execution</h3>
                <div className="space-y-2">
                  {steps.map((step, idx) => <StepRow key={step.id} step={step} index={idx} />)}
                </div>
              </div>
            )}
          </div>

          {/* ── RIGHT COLUMN ── */}
          <div className="lg:col-span-7" ref={resultsRef}>

            {/* Error banner */}
            {error && (
              <div className="mb-6 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-5 py-4 text-sm font-bold text-rose-300">
                ⚠️ {error}
              </div>
            )}

            {!result ? (
              /* Placeholder */
              <div className="flex min-h-[460px] flex-col justify-center rounded-3xl bg-gradient-to-br from-slate-950/90 to-cyan-900/30 p-8 ring-1 ring-white/10 backdrop-blur-md">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-400">Awaiting Upload</p>
                <h2 className="mt-3 text-3xl font-black text-white">Circular AI Engine</h2>
                <p className="mt-2 text-sm text-slate-400 max-w-md leading-relaxed">
                  Our multi-stage pipeline reads micro-textures, fibre structures, and structural anomalies to generate precision recovery actions automatically.
                </p>
                <div className="mt-8 grid gap-4 sm:grid-cols-2">
                  {[
                    { e: "🎨", t: "Texture Edge Detection",  d: "Maps smooth vs rough weave using local pixel variance." },
                    { e: "🔬", t: "Defect & Tear Scans",     d: "Recognises micro-punctures and chemical discolouration." },
                    { e: "🧵", t: "Material Composition",    d: "Infers fabric blends with confidence scoring." },
                    { e: "♻️", t: "Recovery Recommendations",d: "Suggests chemical recycling, mechanical spinning, or reuse." },
                  ].map(f => (
                    <div key={f.t} className="rounded-2xl bg-white/5 p-4 ring-1 ring-white/8">
                      <p className="text-lg">{f.e}</p>
                      <p className="mt-1 text-sm font-bold text-white">{f.t}</p>
                      <p className="mt-1 text-xs text-slate-400 leading-relaxed">{f.d}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* Results */
              <div className="space-y-6">

                {/* Image hero card */}
                <div className="relative overflow-hidden rounded-3xl ring-1 ring-white/10">
                  <img src={imageUrl} alt="Analysed textile" className="h-52 w-full object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/30 to-transparent" />
                  <div className="absolute inset-0 flex items-center px-6">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Identified Fabric</p>
                      <p className="mt-1 text-3xl font-black text-white">{result.material.fabric_type}</p>
                      <p className="mt-1 text-sm text-slate-400">
                        Confidence: <span className="font-bold text-cyan-400">{(result.material.confidence * 100).toFixed(0)}%</span>
                      </p>
                    </div>
                  </div>
                  {/* Color swatch */}
                  <div className="absolute right-4 top-4 flex items-center gap-2 rounded-full bg-black/50 px-3 py-1.5 ring-1 ring-white/20 backdrop-blur">
                    <span className="h-3.5 w-3.5 rounded-full border border-white/40"
                      style={{ background: result.features.color_hex }} />
                    <span className="text-xs font-bold text-white">{result.features.color_name}</span>
                  </div>
                </div>

                {/* Tabbed analysis */}
                <div className="rounded-3xl bg-white/5 p-6 ring-1 ring-white/10 backdrop-blur-md">
                  <div className="mb-5 flex items-center justify-between">
                    <div>
                      <h3 className="text-base font-black text-white">AI Analysis Results</h3>
                      <p className="text-xs text-slate-500">Completed via rule-based classification pipeline</p>
                    </div>
                  </div>

                  {/* Tabs */}
                  <div className="mb-5 flex flex-wrap gap-1 rounded-xl bg-black/30 p-1">
                    {[
                      { id: "features",       label: "Visual Features" },
                      { id: "material",       label: "Material & Fiber" },
                      { id: "waste",          label: "Waste Category" },
                      { id: "recommendations",label: "Recommendations" },
                    ].map(tab => (
                      <button
                        key={tab.id}
                        id={`tab-${tab.id}`}
                        onClick={() => setTab(tab.id)}
                        className={`flex-1 rounded-lg px-3 py-2 text-xs font-bold transition ${
                          activeTab === tab.id
                            ? "bg-cyan-500/20 text-cyan-300 ring-1 ring-cyan-500/30"
                            : "text-slate-500 hover:text-slate-300"
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* ── Tab 1: Visual Features ── */}
                  {activeTab === "features" && (
                    <div>
                      <div className="mb-4 grid grid-cols-2 gap-3">
                        {[
                          { label: "Dominant Colour", value: result.features.color_name },
                          { label: "Hex Code",        value: result.features.color_hex },
                          { label: "Weave Pattern",   value: result.features.fabric_pattern },
                          { label: "Surface Texture", value: result.features.fabric_texture },
                        ].map(f => (
                          <div key={f.label} className="rounded-2xl bg-white/5 p-4 ring-1 ring-white/8">
                            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{f.label}</p>
                            <p className="mt-1 text-sm font-bold capitalize text-white">{f.value}</p>
                          </div>
                        ))}
                      </div>
                      <div className="space-y-3">
                        {/* Damage */}
                        <div className="flex gap-3 rounded-2xl bg-white/5 p-4 ring-1 ring-white/8">
                          <span className={`mt-0.5 text-lg ${result.features.damage_detected ? "text-rose-400" : "text-emerald-400"}`}>
                            {result.features.damage_detected ? "⚠️" : "✅"}
                          </span>
                          <div>
                            <p className="text-sm font-bold text-white">
                              Damage — {result.features.damage_detected ? "Detected" : "None Detected"}
                            </p>
                            <p className="text-xs text-slate-400 mt-0.5">{result.features.damage_details}</p>
                          </div>
                        </div>
                        {/* Contamination */}
                        <div className="flex gap-3 rounded-2xl bg-white/5 p-4 ring-1 ring-white/8">
                          <span className={`mt-0.5 text-lg ${result.features.contamination_detected ? "text-rose-400" : "text-emerald-400"}`}>
                            {result.features.contamination_detected ? "🧪" : "✅"}
                          </span>
                          <div>
                            <p className="text-sm font-bold text-white">
                              Contamination — {result.features.contamination_detected ? "Detected" : "Clean"}
                            </p>
                            <p className="text-xs text-slate-400 mt-0.5">{result.features.contamination_details}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* ── Tab 2: Material & Fiber ── */}
                  {activeTab === "material" && (
                    <div className="space-y-4">
                      <div className="flex items-start justify-between rounded-2xl bg-white/5 p-5 ring-1 ring-white/8">
                        <div>
                          <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Identified Fabric</p>
                          <p className="mt-1 text-3xl font-black text-white">{result.material.fabric_type}</p>
                        </div>
                        <div className="rounded-2xl bg-cyan-400/10 px-4 py-3 text-center ring-1 ring-cyan-400/20">
                          <p className="text-xs font-bold uppercase text-slate-500">Confidence</p>
                          <p className="text-2xl font-black text-cyan-400">
                            {(result.material.confidence * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>
                      <div className="rounded-2xl bg-white/5 p-5 ring-1 ring-white/8">
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Fiber Composition</p>
                        <p className="mt-2 text-sm font-bold text-white">{result.material.fiber_composition}</p>
                        <div className="mt-3 flex h-2 w-full overflow-hidden rounded-full bg-white/10">
                          <div className="bg-gradient-to-r from-cyan-400 to-cyan-600 transition-all"
                            style={{ width: result.material.blend_type === "single" ? "100%" : "60%" }} />
                          {result.material.blend_type === "mixed" && (
                            <div className="bg-gradient-to-r from-emerald-400 to-emerald-600" style={{ width: "40%" }} />
                          )}
                        </div>
                        <p className="mt-1.5 text-xs capitalize text-slate-500">{result.material.blend_type} blend</p>
                      </div>
                      <div className="flex items-center justify-between rounded-2xl bg-white/5 px-5 py-4 ring-1 ring-white/8">
                        <p className="text-sm font-bold text-slate-400">Material Quality Grade</p>
                        <span className={`rounded-full border px-3 py-1 text-xs font-black uppercase tracking-wider ${QUALITY_BADGE[result.material.quality] || ""}`}>
                          {result.material.quality} quality
                        </span>
                      </div>
                    </div>
                  )}

                  {/* ── Tab 3: Waste Category ── */}
                  {activeTab === "waste" && (
                    <div className="space-y-4">
                      <div className="flex items-start justify-between rounded-2xl bg-white/5 p-5 ring-1 ring-white/8">
                        <div>
                          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Waste Category</p>
                          <span className={`inline-flex items-center gap-1.5 rounded-full border px-4 py-1.5 text-sm font-black ${catBadge}`}>
                            {catIcon} {result.waste_classification.category}
                          </span>
                        </div>
                        <div className="text-right">
                          <p className="text-xs font-bold uppercase text-slate-500">Reuse Potential</p>
                          <p className={`mt-1 text-2xl font-black ${REUSE_COLOR[result.waste_classification.reuse_potential] || "text-white"}`}>
                            {result.waste_classification.reuse_potential}
                          </p>
                        </div>
                      </div>
                      <div className="rounded-2xl bg-white/5 p-5 ring-1 ring-white/8">
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Recommended Disposal Method</p>
                        <p className="text-sm font-semibold text-slate-200 leading-relaxed">
                          {result.waste_classification.disposal_method}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* ── Tab 4: Recommendations ── */}
                  {activeTab === "recommendations" && (
                    <div>
                      <p className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500">
                        Circular Economy Recovery Actions
                      </p>
                      <div className="space-y-3">
                        {result.recommendations.map((rec, idx) => {
                          const [title, ...rest] = rec.split(": ");
                          const body = rest.join(": ");
                          const icons = ["🔬","⚙️","🧪","👕","🎨","🤝","🏭","💡"];
                          return (
                            <div key={idx}
                              className="flex gap-3 rounded-2xl bg-white/5 p-4 ring-1 ring-white/8 transition hover:bg-cyan-400/5 hover:ring-cyan-400/20">
                              <span className="shrink-0 text-xl">{icons[idx % icons.length]}</span>
                              <div>
                                <p className="text-sm font-bold text-cyan-300">{title}</p>
                                {body && <p className="mt-1 text-xs text-slate-400 leading-relaxed">{body}</p>}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
