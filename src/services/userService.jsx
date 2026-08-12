import API from "./api";

export const getUsers = () => API.get("/user/users");

export const deleteUser = (id) => API.delete(`/user/users/${id}`);
export const getSystemStatus = () => API.get("/api/admin/system-status");
