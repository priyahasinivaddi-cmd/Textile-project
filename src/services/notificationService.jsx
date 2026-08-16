import API from "./api";

export const getNotifications = () => API.get("/api/notifications");
export const createAnnouncement = (data) => API.post("/api/notifications/announcements", data);
export const removeAnnouncement = (id) => API.delete(`/api/notifications/announcements/${id}`);
export const markNotificationRead = (id) => API.post(`/api/notifications/${encodeURIComponent(id)}/read`);
export const markAllNotificationsRead = () => API.post("/api/notifications/read-all");
