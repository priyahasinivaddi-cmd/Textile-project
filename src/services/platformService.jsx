import API from "./api";

export const globalSearch = (q) => API.get("/api/v1/search", { params: { q } });
export const getModelInsights = () => API.get("/api/v1/models/insights");
export const getModelRegistry = () => API.get("/api/v1/models/registry");
export const syncModelRegistry = () => API.post("/api/v1/models/registry/sync");
export const promoteModel = (id) => API.post(`/api/v1/models/registry/${id}/promote`);
export const getTrainingFeedback = () => API.get("/api/analyses/feedback");
export const downloadTrainingFeedback = () => API.get("/api/analyses/feedback.csv", { responseType: "blob" });
