import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { predictTextileComposition } from "../services/modelService";


const allowedTypes = ["image/png", "image/jpeg", "image/jpg"];

function TextileComposition() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const chooseFile = (event) => {
    const selected = event.target.files?.[0] || null;
    setError("");
    setResult(null);
    setPreview("");
    if (selected && !allowedTypes.includes(selected.type)) {
      setFile(null);
      event.target.value = "";
      setError("Please select a PNG, JPG, or JPEG image.");
      return;
    }
    if (selected && selected.size > 10 * 1024 * 1024) {
      setFile(null);
      event.target.value = "";
      setError("Please select an image that is 10 MB or smaller.");
      return;
    }
    setFile(selected);
    if (selected) setPreview(URL.createObjectURL(selected));
  };

  const predict = async () => {
    if (!file) {
      setError("Select a textile image before predicting.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await predictTextileComposition(file);
      setResult(response.data);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Prediction failed. Check that the backend and model are available.",
      );
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview("");
    setResult(null);
    setError("");
  };

  const composition = result ? Object.entries(result.predicted_composition) : [];

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div className="text-left">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-cyan-600">AI material analysis</p>
            <h1 className="mt-2 text-3xl font-black text-slate-950 sm:text-4xl">Textile Composition Prediction</h1>
            <p className="mt-2 text-sm text-slate-600">Estimate fibre percentages from a close, well-lit fabric image.</p>
          </div>
          <Link to="/dashboard" className="rounded-2xl bg-white px-4 py-3 text-sm font-bold text-slate-700 shadow ring-1 ring-slate-200">
            Back to dashboard
          </Link>
        </div>

        <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <section className="rounded-3xl bg-white p-6 text-left shadow-xl ring-1 ring-slate-200">
            <h2 className="text-2xl font-black text-slate-950">Upload fabric image</h2>
            <p className="mt-2 text-sm text-slate-500">Supported formats: PNG, JPG and JPEG. Maximum size: 10 MB.</p>

            <label className="mt-5 block cursor-pointer rounded-2xl border-2 border-dashed border-cyan-200 bg-cyan-50/60 p-5 text-center transition hover:border-cyan-400">
              <span className="font-bold text-cyan-800">Choose an image</span>
              <input className="sr-only" type="file" accept=".png,.jpg,.jpeg,image/png,image/jpeg" onChange={chooseFile} />
            </label>

            {preview && (
              <div className="mt-5 overflow-hidden rounded-2xl bg-slate-100 ring-1 ring-slate-200">
                <img src={preview} alt="Selected textile preview" className="h-72 w-full object-cover" />
              </div>
            )}
            {file && <p className="mt-3 truncate text-sm font-semibold text-slate-600">{file.name}</p>}
            {error && <p className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700">{error}</p>}

            <div className="mt-5 flex gap-3">
              <button
                type="button"
                onClick={predict}
                disabled={!file || loading}
                className="flex-1 rounded-2xl bg-gradient-to-r from-cyan-600 to-emerald-500 px-5 py-3 font-black text-white shadow-lg shadow-cyan-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "Analysing image..." : "Predict Composition"}
              </button>
              <button type="button" onClick={reset} disabled={loading} className="rounded-2xl bg-slate-100 px-5 py-3 font-bold text-slate-700 disabled:opacity-50">
                Reset
              </button>
            </div>
          </section>

          <section className="rounded-3xl bg-white p-6 text-left shadow-xl ring-1 ring-slate-200">
            {!result ? (
              <div className="flex min-h-96 items-center justify-center rounded-2xl bg-slate-50 p-8 text-center">
                <div>
                  <p className="text-lg font-black text-slate-700">Prediction results will appear here</p>
                  <p className="mt-2 text-sm text-slate-500">Upload a clear fabric photograph to begin.</p>
                </div>
              </div>
            ) : (
              <>
                <div className="rounded-2xl bg-gradient-to-r from-slate-950 to-cyan-900 p-5 text-white">
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-300">Dominant fibre</p>
                  <p className="mt-2 text-3xl font-black capitalize">{result.dominant_fibre}</p>
                  <p className="mt-2 text-sm text-slate-300">Total predicted percentage: <strong className="text-white">{result.total_percentage.toFixed(2)}%</strong></p>
                </div>

                <div className="mt-5 space-y-3">
                  {composition.map(([fibre, percentage]) => (
                    <div key={fibre}>
                      <div className="mb-1 flex justify-between gap-3 text-sm">
                        <span className="font-bold capitalize text-slate-700">{fibre.replaceAll("_", " ")}</span>
                        <span className="font-black text-cyan-700">{Number(percentage).toFixed(2)}%</span>
                      </div>
                      <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                        <div className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500" style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

export default TextileComposition;
