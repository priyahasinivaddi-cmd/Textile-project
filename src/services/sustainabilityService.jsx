import API from "./api";

export const getSustainabilitySummary = () => API.get("/api/analytics/sustainability-summary");
export const getMonthlySustainabilityTrends = () => API.get("/api/analytics/monthly-trends");
export const getAssessments = () => API.get("/api/assessments");
export const calculateAssessment = (batchId) => API.post(`/api/assessments/${batchId}/calculate`);
export const calculateAssessmentsInBackground = () => API.post("/api/assessments/bulk/calculate");
export const downloadSustainabilityPdf = () => API.get("/api/reports/sustainability/pdf", { responseType: "blob" });
export const downloadSustainabilityExcel = () => API.get("/api/reports/sustainability/excel", { responseType: "blob" });
export const downloadSustainabilityCsv = () => API.get("/api/reports/sustainability/csv", { responseType: "blob" });
export const downloadDedicatedReport = (reportType, format) =>
  API.get(`/api/reports/${reportType}/${format}`, { responseType: "blob" });
