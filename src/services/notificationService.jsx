import API from "./api";

export const getNotifications = () => API.get("/api/notifications");
export const createAnnouncement = (data) => API.post("/api/notifications/announcements", data);
export const removeAnnouncement = (id) => API.delete(`/api/notifications/announcements/${id}`);
