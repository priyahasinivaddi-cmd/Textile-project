import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCompositionModelStatus, predictTextileComposition } from "../services/modelService";

const allowedTypes = ["image/png", "image/jpeg", "image/jpg"];

function TextileComposition() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [modelStatus, setModelStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  useEffect(() => {
    let active = true;
    getCompositionModelStatus().then((response) => { if (active) setModelStatus(response.data); }).catch(() => { if (active) setModelStatus({ model_loaded: false }); }).finally(() => { if (active) setStatusLoading(false); });
    return () => { active = false; };
  }, []);

  const chooseFile = (event) => {
    const selected = event.target.files?.[0] || null;
    setError(""); setResult(null); setPreview("");
    if (selected && !allowedTypes.includes(selected.type)) {
      setFile(null); event.target.value = ""; setError("Please select a PNG, JPG, or JPEG image."); return;
    }
    if (selected && selected.size > 10 * 1024 * 1024) {
      setFile(null); event.target.value = ""; setError("Please select an image that is 10 MB or smaller."); return;
    }
    setFile(selected);
    if (selected) setPreview(URL.createObjectURL(selected));
  };

  const predict = async () => {
    if (!file) { setError("Select a textile image before predicting."); return; }
    setLoading(true); setError(""); setResult(null);
    try {
      const response = await predictTextileComposition(file);
      setResult(response.data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Prediction failed. Check that the backend and model are available.");
    } finally { setLoading(false); }
  };

  const reset = () => { setFile(null); setPreview(""); setResult(null); setError(""); };

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div className="text-left">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-cyan-600">AI material analysis</p>
            <h1 className="mt-2 text-3xl font-black text-slate-950 sm:text-4xl">Textile Composition Prediction</h1>
            <p className="mt-2 text-sm text-slate-600">Identify the dominant fibre from a close, well-lit fabric image.</p>
          </div>
          <Link to="/dashboard" className="rounded-2xl bg-white px-4 py-3 text-sm font-bold text-slate-700 shadow ring-1 ring-slate-200">Back to dashboard</Link>
        </div>
        <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <section className="rounded-3xl bg-white p-6 text-left shadow-xl ring-1 ring-slate-200">
            <h2 className="text-2xl font-black text-slate-950">Upload fabric image</h2>
            <p className="mt-2 text-sm text-slate-500">Supported formats: PNG, JPG and JPEG. Maximum size: 10 MB.</p>
            <div className={`mt-4 flex items-center justify-between rounded-2xl px-4 py-3 text-sm ${modelStatus?.model_loaded ? "bg-emerald-50 text-emerald-800" : statusLoading ? "bg-slate-50 text-slate-600" : "bg-rose-50 text-rose-800"}`}>
              <span className="font-bold">{statusLoading ? "Checking trained model..." : modelStatus?.model_loaded ? "Trained model ready" : "Model unavailable"}</span>
              {modelStatus?.model_loaded && <span>{modelStatus.class_name_count} fibre classes</span>}
            </div>
            <label className="mt-5 block cursor-pointer rounded-2xl border-2 border-dashed border-cyan-200 bg-cyan-50/60 p-5 text-center transition hover:border-cyan-400">
              <span className="font-bold text-cyan-800">Choose an image</span>
              <input className="sr-only" type="file" accept=".png,.jpg,.jpeg,image/png,image/jpeg" onChange={chooseFile} />
            </label>
            {preview && <div className="mt-5 overflow-hidden rounded-2xl bg-slate-100 ring-1 ring-slate-200"><img src={preview} alt="Selected textile preview" className="h-72 w-full object-cover" /></div>}
            {file && <p className="mt-3 truncate text-sm font-semibold text-slate-600">{file.name}</p>}
            {error && <p className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700">{error}</p>}
            <div className="mt-5 flex gap-3">
              <button type="button" onClick={predict} disabled={!file || loading || !modelStatus?.model_loaded} className="flex-1 rounded-2xl bg-gradient-to-r from-cyan-600 to-emerald-500 px-5 py-3 font-black text-white shadow-lg shadow-cyan-200 disabled:cursor-not-allowed disabled:opacity-50">{loading ? "Analysing image..." : "Predict Fabric"}</button>
              <button type="button" onClick={reset} disabled={loading} className="rounded-2xl bg-slate-100 px-5 py-3 font-bold text-slate-700 disabled:opacity-50">Reset</button>
            </div>
          </section>
          <section className="rounded-3xl bg-white p-6 text-left shadow-xl ring-1 ring-slate-200">
            {!result ? (
              <div className="flex min-h-96 items-center justify-center rounded-2xl bg-slate-50 p-8 text-center"><div><p className="text-lg font-black text-slate-700">Prediction results will appear here</p><p className="mt-2 text-sm text-slate-500">Upload a clear fabric photograph to begin.</p></div></div>
            ) : (
              <>
                <div className="rounded-2xl bg-gradient-to-r from-slate-950 to-cyan-900 p-5 text-white">
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-300">Predicted fabric</p>
                  <p className="mt-2 text-3xl font-black">{result.predicted_fabric}</p>
                  <p className="mt-2 text-sm text-slate-300">Confidence: <strong className="text-white">{Number(result.confidence).toFixed(2)}%</strong></p>
                  {result.low_confidence && <p className="mt-3 rounded-xl bg-amber-400/15 px-3 py-2 text-sm font-bold text-amber-200">{result.message}</p>}
                </div>
                <div className="mt-5 space-y-3">
                  {(result.top_predictions || []).map((prediction) => (
                    <div key={prediction.fabric}>
                      <div className="mb-1 flex justify-between gap-3 text-sm"><span className="font-bold text-slate-700">{prediction.fabric}</span><span className="font-black text-cyan-700">{Number(prediction.confidence).toFixed(2)}%</span></div>
                      <div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500" style={{ width: `${Math.min(100, Math.max(0, prediction.confidence))}%` }} /></div>
                    </div>
                  ))}
                </div>
                <div className="mt-6 rounded-2xl bg-slate-50 p-4 ring-1 ring-slate-200">
                  <p className="text-sm font-black text-slate-800">How to use this result</p>
                  <p className="mt-1 text-sm text-slate-600">Treat predictions below {modelStatus?.confidence_threshold_percent || 60}% as uncertain and verify them manually before making recycling or disposal decisions.</p>
                </div>
              </>
            )}
          </section>
        </div>
        <section className="mt-6 grid gap-4 rounded-3xl bg-slate-950 p-6 text-left text-white shadow-xl sm:grid-cols-2 lg:grid-cols-4">
          <div><p className="text-xs uppercase tracking-wider text-cyan-300">Production model</p><p className="mt-2 font-black">{modelStatus?.model_artifact || "best_fabric_model.keras"}</p></div>
          <div><p className="text-xs uppercase tracking-wider text-cyan-300">Validation accuracy</p><p className="mt-2 text-2xl font-black">{modelStatus?.training_metrics?.validation_accuracy_percent ?? "—"}%</p></div>
          <div><p className="text-xs uppercase tracking-wider text-cyan-300">Training epochs</p><p className="mt-2 text-2xl font-black">{modelStatus?.training_metrics?.epochs_completed ?? "—"}</p></div>
          <div><p className="text-xs uppercase tracking-wider text-cyan-300">Image guidance</p><p className="mt-2 text-sm text-slate-300">Use a close, evenly lit photo with one fabric filling the frame.</p></div>
        </section>
      </div>
    </main>
  );
}

export default TextileComposition;
