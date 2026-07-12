import API from "./api";

export const getUsers = () => API.get("/user/users");

export const deleteUser = (id) => API.delete(`/user/users/${id}`);
