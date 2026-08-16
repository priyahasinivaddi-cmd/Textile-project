import API from "./api";

/**
 * Sends a textile image file to the backend to be analyzed by the AI pipeline.
 * @param {File} file The image file to analyze
 * @param {number} sensitivity The detection sensitivity (0.0 to 1.0)
 * @returns {Promise} Axios promise with the analysis results
 */
const wait = (ms) => new Promise(resolve => window.setTimeout(resolve, ms));

export const analyzeImage = async (file, sensitivity = 0.5, labelText = "", onProgress = () => {}) => {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("sensitivity", sensitivity);
  if (labelText.trim()) formData.append("label_text", labelText.trim());

  const { data: queued } = await API.post("/api/v1/analysis/jobs", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  onProgress(queued);
  for (;;) {
    await wait(800);
    const { data: job } = await API.get(`/api/v1/analysis/jobs/${queued.job_id}`);
    onProgress(job);
    if (job.status === "complete") return { data: job.result };
    if (job.status === "failed") throw Object.assign(new Error(job.error), { response: { data: { detail: job.error } } });
  }
};

export const reviewAnalysis = (analysisId, payload) =>
  API.post(`/api/analyses/${analysisId}/review`, payload);

export const getAnalysisHistory = (skip = 0, limit = 50) =>
  API.get("/api/analyses", { params: { skip, limit } });

export const getAnalysisJobs = (skip = 0, limit = 25) => API.get("/api/v1/analysis/jobs", { params: { skip, limit } });
