import { useState, useRef } from "react";
import { analyzeImage } from "../services/pipelineService";
import { createInventoryItem } from "../services/inventoryService";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

function UploadWaste() {
  const { user } = useAuth();
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [sensitivity, setSensitivity] = useState(50); // slider range 0-100 mapped to 0.0-1.0
  const [labelText, setLabelText] = useState("");
  
  // Pipeline status states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [pipelineSteps, setPipelineSteps] = useState([
    { label: "Image Upload", status: "idle" },
    { label: "Feature Extraction", status: "idle" },
    { label: "Material Detection", status: "idle" },
    { label: "Waste Classification", status: "idle" },
    { label: "Recommendations", status: "idle" },
  ]);

  // Results state
  const [analysisResult, setAnalysisResult] = useState(null);
  const [activeTab, setActiveTab] = useState("features");
  const [confirmingCandidate, setConfirmingCandidate] = useState("");

  // Inventory Save Form state
  const [registerForm, setRegisterForm] = useState({
    source: "",
    quantity: "",
    collection_date: new Date().toISOString().slice(0, 10),
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState("");

  const fileInputRef = useRef(null);

  // Drag and drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selectedFile = e.dataTransfer.files[0];
      if (selectedFile.type.startsWith("image/")) {
        setFile(selectedFile);
        setPreviewUrl(URL.createObjectURL(selectedFile));
        setAnalysisResult(null);
        setSaveSuccess(false);
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      setAnalysisResult(null);
      setSaveSuccess(false);
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current.click();
  };

  const clearUpload = () => {
    setFile(null);
    setPreviewUrl(null);
    setAnalysisResult(null);
    setSaveSuccess(false);
    setLabelText("");
  };

  // Run the analysis pipeline
  const runPipeline = async () => {
    if (!file) return;

    setIsAnalyzing(true);
    setSaveSuccess(false);
    setSaveError("");
    
    // Reset steps
    const steps = [
      { label: "Image Upload", status: "loading" },
      { label: "Feature Extraction", status: "idle" },
      { label: "Material Detection", status: "idle" },
      { label: "Waste Classification", status: "idle" },
      { label: "Recommendations", status: "idle" },
    ];
    setPipelineSteps(steps);
    setActiveStep(0);

    const updateStep = (index, status) => {
      setPipelineSteps(prev => prev.map((step, idx) => 
        idx === index ? { ...step, status } : step
      ));
      setActiveStep(index);
    };

    try {
      // Step 1: Uploading
      updateStep(0, "loading");
      await new Promise(resolve => setTimeout(resolve, 800)); // micro-interaction delay
      updateStep(0, "success");

      // Step 2: Feature Extraction
      updateStep(1, "loading");
      const sensValue = sensitivity / 100.0;
      const response = await analyzeImage(file, sensValue, labelText);
      const data = response.data;
      await new Promise(resolve => setTimeout(resolve, 1000));
      updateStep(1, "success");

      // Step 3: Material Detection
      updateStep(2, "loading");
      await new Promise(resolve => setTimeout(resolve, 800));
      updateStep(2, "success");

      // Step 4: Waste Classification
      updateStep(3, "loading");
      await new Promise(resolve => setTimeout(resolve, 800));
      updateStep(3, "success");

      // Step 5: Recommendations
      updateStep(4, "loading");
      await new Promise(resolve => setTimeout(resolve, 600));
      updateStep(4, "success");

      setAnalysisResult(data);
    } catch (err) {
      console.error(err);
      // Mark current step as failed
      setPipelineSteps(prev => prev.map((step, idx) => 
        idx === activeStep ? { ...step, status: "error" } : step
      ));
      setSaveError(err.response?.data?.detail || "AI analysis pipeline failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const confirmMaterialCandidate = async (fabric) => {
    if (!file || confirmingCandidate) return;
    setConfirmingCandidate(fabric);
    setSaveError("");
    try {
      const response = await analyzeImage(file, sensitivity / 100.0, `100% ${fabric}`);
      setAnalysisResult(response.data);
      setLabelText(`100% ${fabric}`);
    } catch (err) {
      setSaveError(err.response?.data?.detail || "Could not confirm this material.");
    } finally {
      setConfirmingCandidate("");
    }
  };

  // Save the analyzed batch
  const handleSaveToInventory = async (e) => {
    e.preventDefault();
    if (!analysisResult) return;

    setIsSaving(true);
    setSaveError("");

    // Map Waste Category to suitable inventory Condition string
    let mappedCondition = "Reusable";
    const category = analysisResult.waste_classification.category;
    if (category === "Recyclable") mappedCondition = "Recyclable";
    else if (category === "Hazardous" || category === "Compostable") mappedCondition = "Mixed";
    else if (category === "Repairable" || category === "Upcyclable") mappedCondition = "Damaged";

    const payload = {
      fabric_type: analysisResult.material.fabric_type,
      source: registerForm.source,
      quantity: registerForm.quantity,
      color: analysisResult.features.color_name,
      condition: mappedCondition,
      collection_date: registerForm.collection_date,
      status: "Pending",
      uploaded_by: user?.role === "operator" ? "Recycling Facility" : "Manufacturer",
      assigned_to: "Recycling Facility",
      image_url: analysisResult.image_url,
      analysis_results: JSON.stringify(analysisResult),
    };

    try {
      await createInventoryItem(payload);
      setSaveSuccess(true);
      // Reset form
      setRegisterForm({
        source: "",
        quantity: "",
        collection_date: new Date().toISOString().slice(0, 10),
      });
    } catch (err) {
      console.error(err);
      const detail = err.response?.data?.detail;
      setSaveError(
        typeof detail === "string"
          ? detail
          : "Failed to save inventory record. Please verify fields and try again."
      );
    } finally {
      setIsSaving(false);
    }
  };

  // Helper colors for waste categories
  const getCategoryColor = (category) => {
    switch (category) {
      case "Reusable": return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "Repairable": return "bg-sky-100 text-sky-800 border-sky-300";
      case "Upcyclable": return "bg-purple-100 text-purple-800 border-purple-300";
      case "Recyclable": return "bg-cyan-100 text-cyan-800 border-cyan-300";
      case "Compostable": return "bg-lime-100 text-lime-800 border-lime-300";
      case "Hazardous": return "bg-rose-100 text-rose-800 border-rose-300";
      default: return "bg-slate-100 text-slate-800 border-slate-300";
    }
  };

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* Header Section */}
        <header className="mb-8 flex flex-col gap-4 rounded-3xl bg-white/85 p-6 shadow-xl shadow-slate-200/50 ring-1 ring-slate-100 backdrop-blur-md md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-cyan-600">
              AI circular pipeline
            </p>
            <h1 className="mt-2 text-3xl font-black text-slate-900 sm:text-4xl">
              Textile Upload & Analysis
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Upload an image of textile scraps to analyze fibers, grade quality, detect damage, and generate recycling paths.
            </p>
          </div>
          <Link
            to="/dashboard"
            className="self-start rounded-2xl bg-slate-900 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-slate-300 transition hover:-translate-y-0.5 hover:bg-slate-800"
          >
            Back to Dashboard
          </Link>
        </header>

        <div className="grid gap-8 lg:grid-cols-12">
          {/* Left Column: Upload Dropzone & sensitivity Controls (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-100">
              <h2 className="text-xl font-black text-slate-900 mb-4">Textile Upload</h2>
              
              {/* Dropzone */}
              {!previewUrl ? (
                <div
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                  onClick={triggerFileSelect}
                  className="group relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center cursor-pointer transition hover:border-cyan-500 hover:bg-cyan-50/20"
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept="image/*"
                    className="hidden"
                  />
                  <div className="rounded-full bg-cyan-100 p-4 text-cyan-600 transition group-hover:scale-110">
                    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                    </svg>
                  </div>
                  <h3 className="mt-4 text-lg font-bold text-slate-800">
                    Drag and drop textile image
                  </h3>
                  <p className="mt-2 text-xs text-slate-500 px-6">
                    Supports PNG, JPG, JPEG. Optimal resolution 800x800 for fiber texture analysis.
                  </p>
                  <button className="mt-4 rounded-xl bg-cyan-600 hover:bg-cyan-700 px-4 py-2 text-xs font-bold text-white shadow transition">
                    Browse Files
                  </button>
                </div>
              ) : (
                <div className="relative rounded-2xl overflow-hidden border border-slate-200 bg-slate-900/5">
                  <img
                    src={previewUrl}
                    alt="Textile scrap preview"
                    className="w-full h-64 object-cover"
                  />
                  <button
                    onClick={clearUpload}
                    disabled={isAnalyzing}
                    className="absolute top-3 right-3 rounded-full bg-slate-900/80 hover:bg-slate-900 px-3 py-1.5 text-xs font-bold text-white backdrop-blur transition"
                  >
                    Clear Image
                  </button>
                </div>
              )}

              {/* Sensitivity Configuration Slider */}
              <div className="mt-6 border-t border-slate-100 pt-6">
                <div className="flex justify-between items-center mb-2">
                  <label htmlFor="sensitivity" className="text-sm font-bold text-slate-700">
                    AI Defect Sensitivity
                  </label>
                  <span className="rounded-full bg-cyan-50 px-2.5 py-0.5 text-xs font-black text-cyan-700">
                    {sensitivity}%
                  </span>
                </div>
                <input
                  id="sensitivity"
                  type="range"
                  min="0"
                  max="100"
                  value={sensitivity}
                  onChange={(e) => setSensitivity(Number(e.target.value))}
                  disabled={isAnalyzing}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-cyan-600"
                />
                <p className="mt-1.5 text-xs text-slate-500">
                  Higher sensitivity flags micro-tears (damage) and light stains (contamination) more aggressively.
                </p>
              </div>

              <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4">
                <label htmlFor="label-composition" className="block text-sm font-black text-slate-800">
                  Care-label composition <span className="font-medium text-slate-500">(recommended)</span>
                </label>
                <p className="mt-1 text-xs text-slate-600">
                  Enter the printed label for a more reliable result. Leave blank for image-only estimation.
                </p>
                <textarea
                  id="label-composition"
                  value={labelText}
                  onChange={(event) => setLabelText(event.target.value)}
                  disabled={isAnalyzing}
                  rows={2}
                  placeholder="Example: 80% Cotton, 20% Polyester"
                  className="mt-3 w-full resize-none rounded-xl border border-emerald-200 bg-white px-3 py-2 text-sm font-semibold text-slate-800 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                />
              </div>

              {/* Action Button */}
              <button
                onClick={runPipeline}
                disabled={!file || isAnalyzing}
                className="mt-6 w-full flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-600 to-emerald-500 disabled:from-slate-300 disabled:to-slate-400 py-3.5 px-4 text-sm font-black text-white shadow-lg shadow-cyan-100 transition hover:-translate-y-0.5 hover:shadow-cyan-200"
              >
                {isAnalyzing ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Processing Engine...</span>
                  </>
                ) : (
                  <>
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span>Run Analysis Pipeline</span>
                  </>
                )}
              </button>
            </div>

            {/* Stepper progress (Only visible when active/running) */}
            {(isAnalyzing || pipelineSteps.some(s => s.status !== "idle")) && (
              <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-100">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4">Pipeline Execution</h3>
                <div className="space-y-4">
                  {pipelineSteps.map((step, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold border 
                          ${step.status === "loading" ? "border-cyan-600 bg-cyan-50 text-cyan-600 animate-pulse" : ""}
                          ${step.status === "success" ? "border-emerald-600 bg-emerald-50 text-emerald-600" : ""}
                          ${step.status === "error" ? "border-rose-600 bg-rose-50 text-rose-600" : ""}
                          ${step.status === "idle" ? "border-slate-300 bg-slate-50 text-slate-400" : ""}
                        `}>
                          {step.status === "success" ? "✓" : step.status === "error" ? "✕" : idx + 1}
                        </div>
                        <span className={`text-sm font-bold ${step.status === "loading" ? "text-cyan-700 animate-pulse" : "text-slate-700"}`}>
                          {step.label}
                        </span>
                      </div>
                      <div>
                        {step.status === "loading" && (
                          <span className="text-xs bg-cyan-100 text-cyan-800 px-2 py-0.5 rounded font-semibold">Running</span>
                        )}
                        {step.status === "success" && (
                          <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">Complete</span>
                        )}
                        {step.status === "error" && (
                          <span className="text-xs bg-rose-100 text-rose-800 px-2 py-0.5 rounded font-semibold">Failed</span>
                        )}
                        {step.status === "idle" && (
                          <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded font-semibold">Queued</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: AI Outputs or Instructions (7 cols) */}
          <div className="lg:col-span-7">
            {saveError && (
              <div className="mb-6 rounded-2xl bg-rose-50 border border-rose-200 px-5 py-4 text-sm font-bold text-rose-700">
                {saveError}
              </div>
            )}

            {saveSuccess && (
              <div className="mb-6 rounded-3xl bg-emerald-50 border border-emerald-200 p-6 text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-800 font-bold text-xl mb-4">
                  ✓
                </div>
                <h3 className="text-lg font-black text-emerald-950">Batch Successfully Registered</h3>
                <p className="mt-1 text-sm text-emerald-700">
                  The AI-analyzed textile waste batch has been added to your inventory list.
                </p>
                <div className="mt-4 flex justify-center gap-3">
                  <Link
                    to="/inventory"
                    className="rounded-xl bg-slate-900 text-white px-4 py-2 text-xs font-bold shadow hover:bg-slate-800 transition"
                  >
                    View Inventory
                  </Link>
                  <button
                    onClick={clearUpload}
                    className="rounded-xl bg-emerald-100 text-emerald-800 border border-emerald-200 px-4 py-2 text-xs font-bold hover:bg-emerald-200 transition"
                  >
                    Upload Another
                  </button>
                </div>
              </div>
            )}

            {!analysisResult ? (
              /* Informational Mockup / Placeholder state */
              <div className="rounded-3xl bg-gradient-to-br from-slate-950 to-cyan-900 text-white p-8 shadow-xl flex flex-col justify-center h-full min-h-[380px]">
                <h2 className="text-3xl font-black mb-3">Circular AI Engine</h2>
                <p className="text-slate-300 text-sm max-w-lg mb-6 leading-relaxed">
                  Our advanced material detection pipeline reads micro-textures, fibers, and structural anomalies to generate recovery actions automatically.
                </p>
                <div className="grid gap-4 sm:grid-cols-2">
                  {[
                    { title: "Texture Edge Detection", desc: "Maps smooth vs rough weave features using local pixel variance algorithms." },
                    { title: "Defect & Tear Scans", desc: "Recognizes micro-punctures, surface dirt, and chemical discoloration spots." },
                    { title: "Material Composition", desc: "Infers cotton/wool/polyester fabric blends with confidence scoring." },
                    { title: "Recovery Recommendations", desc: "Suggests chemical monomer conversion, mechanical yarn spinning, or mending." }
                  ].map((item, idx) => (
                    <div key={idx} className="bg-white/10 rounded-2xl p-4 border border-white/5 backdrop-blur-sm">
                      <h4 className="font-bold text-white text-sm mb-1">{item.title}</h4>
                      <p className="text-xs text-slate-300 leading-normal">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* Analysis results visualization cards */
              <div className="space-y-6">
                <div className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-100">
                  <div className="flex flex-wrap justify-between items-center border-b border-slate-100 pb-4 mb-4 gap-3">
                    <div>
                      <h3 className="text-lg font-black text-slate-900">AI Analysis Results</h3>
                      <p className="text-xs text-slate-500">Completed via circular neural network classification rules</p>
                    </div>
                    
                    {/* Navigation tabs */}
                    <div className="flex bg-slate-100 rounded-xl p-1 text-xs">
                      {[
                        { id: "features", label: "Visual Features" },
                        { id: "material", label: "Material & Fiber" },
                        { id: "waste", label: "Waste Classification" },
                        { id: "recommendations", label: "Recommendations" }
                      ].map(tab => (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={`px-3 py-1.5 rounded-lg font-bold transition ${activeTab === tab.id ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-800"}`}
                        >
                          {tab.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Tab Contents */}
                  <div className="py-2">
                    {/* Tab 1: Visual Features */}
                    {activeTab === "features" && (
                      <div className="grid gap-5 sm:grid-cols-2">
                        <div className="bg-slate-50 rounded-2xl p-4">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Color & Pattern</h4>
                          <div className="space-y-3">
                            <div className="flex justify-between items-center">
                              <span className="text-sm text-slate-600">Dominant Color</span>
                              <div className="flex items-center gap-2">
                                <span className="h-4.5 w-4.5 rounded-full border border-slate-300 shadow-sm" style={{ backgroundColor: analysisResult.features.color_hex }} />
                                <span className="font-bold text-sm text-slate-800">{analysisResult.features.color_name}</span>
                              </div>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm text-slate-600">Hex Code</span>
                              <code className="text-xs">{analysisResult.features.color_hex}</code>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm text-slate-600">Weave Pattern</span>
                              <span className="font-bold text-sm text-slate-800 capitalize bg-slate-200/50 px-2 py-0.5 rounded">{analysisResult.features.fabric_pattern}</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm text-slate-600">Weave Texture</span>
                              <span className="font-bold text-sm text-slate-800 capitalize bg-slate-200/50 px-2 py-0.5 rounded">{analysisResult.features.fabric_texture}</span>
                            </div>
                          </div>
                        </div>

                        <div className="bg-slate-50 rounded-2xl p-4 space-y-4">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Defects & Contaminants</h4>
                          
                          {/* Damage */}
                          <div className="flex gap-3">
                            <div className={`mt-0.5 rounded-full p-2 h-8 w-8 flex items-center justify-center ${analysisResult.features.damage_detected ? "bg-rose-100 text-rose-700" : "bg-emerald-100 text-emerald-700"}`}>
                              <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                {analysisResult.features.damage_detected ? (
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                ) : (
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                                )}
                              </svg>
                            </div>
                            <div>
                              <p className="text-sm font-bold text-slate-800">
                                Damage (Tears/Holes): {analysisResult.features.damage_detected ? "Detected" : "None Detected"}
                              </p>
                              <p className="text-xs text-slate-500 mt-0.5">{analysisResult.features.damage_details}</p>
                            </div>
                          </div>

                          {/* Contamination */}
                          <div className="flex gap-3 border-t border-slate-200/60 pt-3">
                            <div className={`mt-0.5 rounded-full p-2 h-8 w-8 flex items-center justify-center ${analysisResult.features.contamination_detected ? "bg-rose-100 text-rose-700" : "bg-emerald-100 text-emerald-700"}`}>
                              <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                {analysisResult.features.contamination_detected ? (
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 9.172V5L8 4z" />
                                ) : (
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                                )}
                              </svg>
                            </div>
                            <div>
                              <p className="text-sm font-bold text-slate-800">
                                Stains & Dirt: {analysisResult.features.contamination_detected ? "Detected" : "Clean"}
                              </p>
                              <p className="text-xs text-slate-500 mt-0.5">{analysisResult.features.contamination_details}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Tab 2: Material & Composition */}
                    {activeTab === "material" && (
                      <div className="bg-slate-50 rounded-2xl p-5 space-y-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Identified Fabric</h4>
                            <p className="text-2xl font-black text-slate-900">{analysisResult.material.fabric_type}</p>
                          </div>
                          <div className="text-right">
                            <span className="text-xs font-bold text-slate-500">
                              {analysisResult.material.evidence_source === "care_label" ? "Label confidence" : "Image confidence"}
                            </span>
                            <p className="text-xl font-black text-cyan-600">{(analysisResult.material.confidence * 100).toFixed(0)}%</p>
                          </div>
                        </div>

                        <div className={`rounded-xl border px-3 py-2 text-xs font-bold ${analysisResult.material.evidence_source === "care_label" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-amber-200 bg-amber-50 text-amber-800"}`}>
                          {analysisResult.material.evidence_source === "care_label"
                            ? "Verified from the care-label composition you entered."
                            : "Estimated from the textile image. Verify with a care label when possible."}
                        </div>

                        {analysisResult.material.evidence_source === "image_model" && analysisResult.material.alternatives?.length > 0 && (
                          <div className="rounded-xl border border-cyan-200 bg-cyan-50 p-3">
                            <p className="text-xs font-black text-slate-800">Confirm the closest material</p>
                            <p className="mt-1 text-xs text-slate-600">Your confirmation improves the saved result and recalculates recycling guidance.</p>
                            <div className="mt-3 flex flex-wrap gap-2">
                              {analysisResult.material.alternatives
                                .filter((item) => /cotton|polyester|wool|silk|linen|flax|nylon|rayon|viscose|acrylic|denim/i.test(item.fabric))
                                .map((item) => (
                                  <button
                                    key={item.fabric}
                                    type="button"
                                    disabled={Boolean(confirmingCandidate)}
                                    onClick={() => confirmMaterialCandidate(item.fabric)}
                                    className="rounded-lg border border-cyan-200 bg-white px-3 py-2 text-xs font-bold text-cyan-800 transition hover:border-cyan-500 disabled:opacity-50"
                                  >
                                    {confirmingCandidate === item.fabric ? "Confirming…" : `${item.fabric} (${item.confidence.toFixed(0)}%)`}
                                  </button>
                                ))}
                            </div>
                          </div>
                        )}

                        {/* Composition bar */}
                        <div className="border-t border-slate-200/60 pt-4">
                          <span className="text-xs font-bold text-slate-500">Fibre composition</span>
                          <div className="flex justify-between items-center mt-1">
                            <span className="font-bold text-sm text-slate-800">{analysisResult.material.fiber_composition}</span>
                            <span className="text-xs capitalize font-semibold bg-slate-200/50 px-2 py-0.5 rounded">{analysisResult.material.blend_type} blend</span>
                          </div>
                          
                          {/* Fancy visual bar representation */}
                          <div className="h-3 w-full bg-slate-200 rounded-full overflow-hidden mt-2.5 flex">
                            <div className="bg-cyan-600 h-full" style={{ width: analysisResult.material.blend_type === "single" ? "100%" : "60%" }} />
                            {analysisResult.material.blend_type === "mixed" && (
                              <div className="bg-emerald-500 h-full" style={{ width: "40%" }} />
                            )}
                          </div>
                        </div>

                        <div className="flex justify-between items-center border-t border-slate-200/60 pt-4">
                          <span className="text-xs font-bold text-slate-500">Material Quality Grade</span>
                          <span className={`text-xs font-black uppercase tracking-wider px-3 py-1 rounded-full border
                            ${analysisResult.material.quality === "high" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : ""}
                            ${analysisResult.material.quality === "medium" ? "bg-amber-50 text-amber-700 border-amber-200" : ""}
                            ${analysisResult.material.quality === "low" ? "bg-rose-50 text-rose-700 border-rose-200" : ""}
                          `}>
                            {analysisResult.material.quality} quality
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Tab 3: Waste Classification */}
                    {activeTab === "waste" && (
                      <div className="bg-slate-50 rounded-2xl p-5 space-y-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Waste Category</h4>
                            <span className={`text-sm font-black border px-3 py-1.5 rounded-full ${getCategoryColor(analysisResult.waste_classification.category)}`}>
                              {analysisResult.waste_classification.category}
                            </span>
                          </div>
                          <div className="text-right">
                            <span className="text-xs font-bold text-slate-500">Reuse Potential</span>
                            <p className={`text-lg font-black 
                              ${analysisResult.waste_classification.reuse_potential === "High" ? "text-emerald-600" : ""}
                              ${analysisResult.waste_classification.reuse_potential === "Medium" ? "text-amber-600" : ""}
                              ${analysisResult.waste_classification.reuse_potential === "Low" ? "text-rose-600" : ""}
                            `}>
                              {analysisResult.waste_classification.reuse_potential}
                            </p>
                          </div>
                        </div>

                        <div className="border-t border-slate-200/60 pt-4">
                          <h5 className="text-xs font-bold text-slate-500 mb-1">Recommended Disposal Method</h5>
                          <p className="text-sm font-semibold text-slate-800 leading-relaxed bg-slate-200/30 p-3 rounded-xl border border-slate-200/40">
                            {analysisResult.waste_classification.disposal_method}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Tab 4: Recommendations */}
                    {activeTab === "recommendations" && (
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Recommended Circular Solutions</h4>
                        <div className="grid gap-3">
                          {analysisResult.recommendations.map((recommendation, idx) => (
                            <div key={idx} className="flex gap-3 bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                              <div className="mt-0.5 rounded-full bg-cyan-50 text-cyan-600 p-1.5 h-7 w-7 flex items-center justify-center shrink-0">
                                <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                </svg>
                              </div>
                              <span className="text-sm font-semibold text-slate-700 leading-normal">{recommendation}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Form to Confirm & Save batch */}
                <form onSubmit={handleSaveToInventory} className="rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-100 space-y-5">
                  <div className="border-b border-slate-100 pb-3">
                    <p className="text-xs font-bold uppercase tracking-wider text-emerald-600">Action Required</p>
                    <h3 className="text-lg font-black text-slate-900">Register Waste to Inventory</h3>
                    <p className="text-xs text-slate-500">Pre-filled with AI classification findings. Add quantity and unit source below.</p>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-xs font-bold text-slate-500 mb-1">Fabric Type (AI Detected)</label>
                      <input
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 font-semibold text-slate-800 cursor-not-allowed"
                        type="text"
                        value={analysisResult.material.fabric_type}
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-500 mb-1">Color (AI Detected)</label>
                      <input
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 font-semibold text-slate-800 cursor-not-allowed"
                        type="text"
                        value={analysisResult.features.color_name}
                        readOnly
                      />
                    </div>
                    <div>
                      <label htmlFor="source" className="block text-xs font-bold text-slate-700 mb-1">Source Factory/Unit*</label>
                      <input
                        id="source"
                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-cyan-500 focus:outline-none"
                        placeholder="e.g. Unit 3 Weaving Room"
                        type="text"
                        value={registerForm.source}
                        onChange={(e) => setRegisterForm({ ...registerForm, source: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="quantity" className="block text-xs font-bold text-slate-700 mb-1">Quantity (kg)*</label>
                      <input
                        id="quantity"
                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-cyan-500 focus:outline-none"
                        placeholder="e.g. 150"
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={registerForm.quantity}
                        onChange={(e) => setRegisterForm({ ...registerForm, quantity: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="collection_date" className="block text-xs font-bold text-slate-700 mb-1">Collection/Upload Date*</label>
                      <input
                        id="collection_date"
                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-cyan-500 focus:outline-none"
                        type="date"
                        value={registerForm.collection_date}
                        onChange={(e) => setRegisterForm({ ...registerForm, collection_date: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-500 mb-1">Mapped Condition (AI Mapped)</label>
                      <input
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 font-semibold text-slate-800 cursor-not-allowed"
                        type="text"
                        value={analysisResult.waste_classification.category === "Recyclable" ? "Recyclable" :
                               analysisResult.waste_classification.category === "Reusable" ? "Reusable" :
                               ["Hazardous", "Compostable"].includes(analysisResult.waste_classification.category) ? "Mixed" : "Damaged"}
                        readOnly
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSaving}
                    className="w-full rounded-2xl bg-slate-900 hover:bg-slate-800 disabled:bg-slate-500 py-3.5 px-4 font-black text-white shadow-lg transition hover:-translate-y-0.5"
                  >
                    {isSaving ? "Saving to Database..." : "Confirm & Save to Inventory"}
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

export default UploadWaste;
