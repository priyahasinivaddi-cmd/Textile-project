import API from "./api";

export const getInventory = () => API.get("/inventory");

export const createInventoryItem = (data) => API.post("/inventory", data);

export const updateInventoryItem = (id, data) => API.put(`/inventory/${id}`, data);

export const deleteInventoryItem = (id) => API.delete(`/inventory/${id}`);

export const downloadWasteReport = () =>
  API.get("/inventory/report/pdf", { responseType: "blob" });

export const downloadWasteItemReport = (id) =>
  API.get(`/inventory/${id}/report/pdf`, { responseType: "blob" });
