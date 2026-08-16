import { useState, useRef, useCallback } from "react";
import { Link } from "react-router-dom";
import { analyzeImage, reviewAnalysis } from "../services/pipelineService";
import { createInventoryItem } from "../services/inventoryService";

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
const FABRIC_OPTIONS = ["Cotton", "Polyester", "Wool", "Silk", "Linen", "Denim", "Nylon", "Rayon", "Acrylic", "Mixed Fabrics"];

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
  const [labelText, setLabelText] = useState("");
  const [isDragging, setDrag]   = useState(false);

  const [steps, setSteps]       = useState(() => PIPELINE_STEPS.map(s => ({ ...s, status: "idle" })));
  const [running, setRunning]   = useState(false);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState("");
  const [activeTab, setTab]     = useState("features");
  const [review, setReview] = useState({ decision: "accept", destination: "Reuse", reason: "" });
  const [reviewing, setReviewing] = useState(false);
  const [reviewMessage, setReviewMessage] = useState("");
  const [registerForm, setRegisterForm] = useState({ source: "", quantity: "", collection_date: new Date().toISOString().slice(0, 10) });
  const [saveState, setSaveState] = useState({ saving: false, message: "", error: "" });
  const [confirmedMaterial, setConfirmedMaterial] = useState("");

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

  const runPipeline = async () => {
    if (!file || running) return;
    setRunning(true); setError(""); setResult(null);
    setSteps(PIPELINE_STEPS.map(s => ({ ...s, status: "idle" })));
    try {
      updateStep(0, "loading");
      const { data } = await analyzeImage(file, sensitivity / 100, labelText, (job) => {
        const stageIndex = job.progress < 15 ? 0 : job.progress < 40 ? 1 : job.progress < 70 ? 2 : job.progress < 90 ? 3 : 4;
        setSteps(PIPELINE_STEPS.map((step, index) => ({ ...step, status: index < stageIndex ? "success" : index === stageIndex ? "loading" : "idle" })));
      });
      setSteps(PIPELINE_STEPS.map(step => ({ ...step, status: "success" })));
      setResult(data); setConfirmedMaterial(""); setTab("features");
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 200);
    } catch (err) {
      const msg = err?.response?.data?.detail || "Pipeline failed. Please try another image.";
      setError(msg);
      setSteps(prev => prev.map(s => s.status === "loading" ? { ...s, status: "error" } : s));
    } finally {
      setRunning(false);
    }
  };

  const saveToInventory = async (event) => {
    event.preventDefault();
    if (!result || saveState.saving) return;
    const uncertain = Number(result.material?.confidence || 0) < 0.7 || /uncertain|unknown/i.test(result.material?.fabric_type || "");
    if (uncertain && !confirmedMaterial) {
      setSaveState({ saving: false, message: "", error: "Please confirm the fabric type before saving this uncertain result." });
      return;
    }
    setSaveState({ saving: true, message: "", error: "" });
    try {
      await createInventoryItem({
        fabric_type: confirmedMaterial || result.material?.fabric_type || "Unclassified textile",
        source: registerForm.source,
        quantity: registerForm.quantity,
        color: result.features?.color_name || "Not recorded",
        condition: result.waste_classification?.category || "Pending review",
        collection_date: registerForm.collection_date,
        status: "Pending",
        uploaded_by: "Current user",
        assigned_to: "Recycling Facility",
      });
      setSaveState({ saving: false, message: "Batch saved to inventory.", error: "" });
    } catch (err) {
      setSaveState({ saving: false, message: "", error: err?.response?.data?.detail || "Batch could not be saved." });
    }
  };

  const submitReview = async (event) => {
    event.preventDefault();
    if (!result?.analysis_id || reviewing) return;
    setReviewing(true); setReviewMessage("");
    try {
      const { data } = await reviewAnalysis(result.analysis_id, review);
      setResult(prev => ({ ...prev, review_status: data.review_status, final_destination: data.final_destination }));
      setReviewMessage(`Decision saved: ${data.final_destination}`);
    } catch (err) {
      setReviewMessage(err?.response?.data?.detail || "Review could not be saved.");
    } finally {
      setReviewing(false);
    }
  };

  const catBadge = result ? (CATEGORY_BADGE[result.waste_classification?.category] || CATEGORY_BADGE.Recyclable) : "";
  const catIcon  = result ? (CATEGORY_ICON[result.waste_classification?.category]  || "🔄") : "";
  const materialUncertain = Boolean(result && (Number(result.material?.confidence || 0) < 0.7 || /uncertain|unknown/i.test(result.material?.fabric_type || "")));

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
                <label className="mb-4 grid gap-1.5 text-sm font-bold text-slate-300">Garment label or known composition <span className="font-normal text-slate-500">Optional</span>
                  <input value={labelText} onChange={event => setLabelText(event.target.value)} placeholder="e.g. 80% cotton, 20% polyester" className="rounded-xl bg-white/8 px-3 py-2.5 font-normal text-white ring-1 ring-white/15 placeholder:text-slate-600" />
                </label>
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

                {materialUncertain ? (
                  <section className="rounded-3xl bg-amber-400/10 p-6 ring-1 ring-amber-400/30" aria-labelledby="confirm-fabric-title">
                    <p className="text-xs font-black uppercase tracking-wider text-amber-300">Human confirmation required</p>
                    <h3 id="confirm-fabric-title" className="mt-1 text-xl font-black text-white">The fabric prediction is uncertain</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-300">The AI predicted <strong>{result.material.fabric_type}</strong> at {(result.material.confidence * 100).toFixed(0)}% confidence. Select the fabric you can verify before saving the batch.</p>
                    <label className="mt-4 grid gap-1.5 text-sm font-bold text-amber-100">Confirmed fabric type
                      <select value={confirmedMaterial} onChange={event => { setConfirmedMaterial(event.target.value); setSaveState({ saving: false, message: "", error: "" }); }} className="rounded-xl bg-slate-900 px-4 py-3 text-white ring-1 ring-amber-300/30" required>
                        <option value="">Select fabric type</option>
                        {FABRIC_OPTIONS.map(fabric => <option key={fabric} value={fabric}>{fabric}</option>)}
                      </select>
                    </label>
                    {confirmedMaterial && <p className="mt-3 rounded-xl bg-emerald-400/10 px-3 py-2 text-sm font-bold text-emerald-300">Human-confirmed material: {confirmedMaterial}</p>}
                  </section>
                ) : (
                  <details className="rounded-2xl bg-white/5 p-4 text-sm text-slate-300 ring-1 ring-white/10">
                    <summary className="cursor-pointer font-bold text-cyan-300">Is the predicted fabric incorrect?</summary>
                    <label className="mt-3 grid gap-1.5">Choose the correct fabric type
                      <select value={confirmedMaterial} onChange={event => setConfirmedMaterial(event.target.value)} className="rounded-xl bg-slate-900 px-4 py-3 text-white ring-1 ring-white/20">
                        <option value="">Keep AI prediction: {result.material.fabric_type}</option>
                        {FABRIC_OPTIONS.map(fabric => <option key={fabric} value={fabric}>{fabric}</option>)}
                      </select>
                    </label>
                  </details>
                )}

                <section className="rounded-3xl bg-emerald-400/10 p-6 ring-1 ring-emerald-400/20">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div><p className="text-xs font-black uppercase tracking-wider text-emerald-300">Next step</p><h3 className="mt-1 text-xl font-black text-white">Register this analysed batch</h3><p className="mt-1 text-sm text-slate-400">Confirm its source, quantity{materialUncertain ? ", and fabric" : ""}, then add it to inventory.</p></div>
                    <Link to="/inventory" className="text-sm font-bold text-emerald-300">View inventory →</Link>
                  </div>
                  <form onSubmit={saveToInventory} className="mt-5 grid gap-3 sm:grid-cols-3">
                    <label className="grid gap-1 text-xs font-bold text-slate-300">Source<input required value={registerForm.source} onChange={event => setRegisterForm({ ...registerForm, source: event.target.value })} placeholder="Factory or unit" className="rounded-xl bg-slate-900 px-3 py-2.5 font-normal text-white ring-1 ring-white/20" /></label>
                    <label className="grid gap-1 text-xs font-bold text-slate-300">Quantity<input required value={registerForm.quantity} onChange={event => setRegisterForm({ ...registerForm, quantity: event.target.value })} placeholder="e.g. 24 kg" className="rounded-xl bg-slate-900 px-3 py-2.5 font-normal text-white ring-1 ring-white/20" /></label>
                    <label className="grid gap-1 text-xs font-bold text-slate-300">Collection date<input required type="date" value={registerForm.collection_date} onChange={event => setRegisterForm({ ...registerForm, collection_date: event.target.value })} className="rounded-xl bg-slate-900 px-3 py-2.5 font-normal text-white ring-1 ring-white/20" /></label>
                    <button disabled={saveState.saving || Boolean(saveState.message)} className="rounded-xl bg-emerald-400 px-4 py-2.5 text-sm font-black text-slate-950 disabled:opacity-60 sm:col-span-3">{saveState.message || (saveState.saving ? "Saving…" : "Save batch to inventory")}</button>
                  </form>
                  {saveState.error && <p role="alert" className="mt-3 text-sm font-bold text-rose-300">{saveState.error}</p>}
                </section>

                {result.ai_predictions && (
                  <section className="rounded-3xl bg-white/5 p-6 ring-1 ring-white/10" aria-live="polite">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-bold uppercase tracking-wider text-cyan-400">Development model</p>
                        <h3 className="mt-1 text-lg font-black text-white">{result.ai_predictions.model}</h3>
                        <p className="mt-1 text-xs text-slate-400">Version {result.ai_predictions.model_version}</p>
                      </div>
                      {result.ai_predictions.manual_review_required && (
                        <span className="rounded-full border border-amber-400/40 bg-amber-400/10 px-3 py-1 text-xs font-black text-amber-300">
                          Manual review required
                        </span>
                      )}
                    </div>
                    <div className="mt-5 grid gap-3 sm:grid-cols-2">
                      {Object.entries(result.ai_predictions.predictions || {}).map(([head, prediction]) => (
                        <div key={head} className="rounded-2xl bg-black/20 p-4 ring-1 ring-white/10">
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{head}</p>
                            <p className="text-sm font-black text-cyan-300">{(prediction.confidence * 100).toFixed(1)}%</p>
                          </div>
                          <p className="mt-1 text-xl font-black text-white">{prediction.label}</p>
                          <div className="mt-3 space-y-1.5">
                            {prediction.top_predictions.map((item) => (
                              <div key={item.label} className="flex justify-between text-xs text-slate-400">
                                <span>{item.label}</span><span>{(item.probability * 100).toFixed(1)}%</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="mt-4 rounded-2xl bg-amber-400/10 p-3 text-xs leading-relaxed text-amber-200">
                      {result.ai_predictions.warning}
                    </p>
                    <p className="mt-3 text-xs leading-relaxed text-slate-400">{result.ai_disclaimer}</p>
                  </section>
                )}

                {result.destination_intelligence && (
                  <section className="rounded-3xl bg-white/5 p-6 ring-1 ring-white/10" aria-label="Explainable destination decision">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-bold uppercase tracking-wider text-emerald-400">Fused waste intelligence</p>
                        <h3 className="mt-1 text-2xl font-black text-white">{result.destination_intelligence.destination}</h3>
                        <p className="mt-1 text-sm text-slate-400">Calibrated confidence <span className="font-black text-emerald-300">{(result.destination_intelligence.confidence * 100).toFixed(1)}%</span></p>
                      </div>
                      <details className="text-xs text-slate-400"><summary className="cursor-pointer rounded-full bg-white/10 px-3 py-1 font-bold text-slate-300">How this was calculated</summary><p className="mt-2 max-w-xs rounded-xl bg-slate-950 p-3">The destination score combines 65% batch metadata with 35% visual evidence.</p></details>
                    </div>
                    <div className="mt-5 grid gap-5 lg:grid-cols-2">
                      <div>
                        <p className="text-xs font-black uppercase tracking-wider text-slate-500">Destination probabilities</p>
                        <div className="mt-3 space-y-2">
                          {result.destination_intelligence.probabilities.map(item => (
                            <div key={item.label}>
                              <div className="flex justify-between text-xs text-slate-300"><span>{item.label}</span><span>{(item.probability * 100).toFixed(1)}%</span></div>
                              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-emerald-400" style={{ width: `${item.probability * 100}%` }} /></div>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-xs font-black uppercase tracking-wider text-slate-500">Why this decision</p>
                        <ul className="mt-3 space-y-2 text-sm text-slate-300">
                          {result.destination_intelligence.reasoning.map(reason => <li key={reason} className="rounded-xl bg-black/20 px-3 py-2">{reason}</li>)}
                        </ul>
                      </div>
                    </div>
                    {result.destination_intelligence.manual_review_required && <p className="mt-4 rounded-2xl bg-amber-400/10 p-3 text-xs leading-relaxed text-amber-200">{result.destination_intelligence.warning}</p>}
                  </section>
                )}

                {result.analysis_id && (
                  <section className="rounded-3xl bg-white/5 p-6 ring-1 ring-white/10">
                    <p className="text-xs font-bold uppercase tracking-wider text-emerald-400">Human review</p>
                    <div className="mt-1 flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-lg font-black text-white">Confirm the operational decision</h3>
                      <span className="text-xs text-slate-400">{result.analysis_id}</span>
                    </div>
                    {result.review_status === "pending" ? (
                      <form onSubmit={submitReview} className="mt-4 space-y-3">
                        <div className="grid gap-3 sm:grid-cols-2">
                          <select value={review.decision} onChange={e => setReview({ ...review, decision: e.target.value })} className="rounded-xl bg-slate-900 px-3 py-2 text-sm text-white ring-1 ring-white/20">
                            <option value="accept">Accept AI destination</option>
                            <option value="override">Override destination</option>
                          </select>
                          {review.decision === "override" && (
                            <select value={review.destination} onChange={e => setReview({ ...review, destination: e.target.value })} className="rounded-xl bg-slate-900 px-3 py-2 text-sm text-white ring-1 ring-white/20">
                              {["Reuse", "Export", "Repair", "Remake", "Recycle", "Energy Recovery"].map(value => <option key={value}>{value}</option>)}
                            </select>
                          )}
                        </div>
                        <textarea required minLength={2} maxLength={1000} rows={3} value={review.reason} onChange={e => setReview({ ...review, reason: e.target.value })} placeholder="Reason or reviewer notes" className="w-full rounded-xl bg-slate-900 px-3 py-2 text-sm text-white ring-1 ring-white/20" />
                        <button disabled={reviewing} className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-black text-slate-950 disabled:opacity-50">{reviewing ? "Saving…" : "Confirm decision"}</button>
                      </form>
                    ) : (
                      <p className="mt-4 rounded-xl bg-emerald-400/10 p-3 text-sm font-bold text-emerald-300">{result.review_status}: {result.final_destination}</p>
                    )}
                    {reviewMessage && <p className="mt-3 text-xs text-slate-300" aria-live="polite">{reviewMessage}</p>}
                  </section>
                )}

                {/* Tabbed analysis */}
                <details className="rounded-3xl bg-white/5 p-6 ring-1 ring-white/10 backdrop-blur-md">
                  <summary className="cursor-pointer text-base font-black text-white">Advanced analysis details</summary>
                  <div className="mt-5">
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
                </details>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
