import API from "./api";

export const getInventory = () => API.get("/inventory");

export const createInventoryItem = (data) => API.post("/inventory", data);

export const updateInventoryItem = (id, data) => API.put(`/inventory/${id}`, data);

export const deleteInventoryItem = (id) => API.delete(`/inventory/${id}`);
