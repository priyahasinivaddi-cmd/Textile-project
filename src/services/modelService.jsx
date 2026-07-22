import API from "./api";


export const predictTextileComposition = (image) => {
  const formData = new FormData();
  formData.append("file", image);
  return API.post("/api/model/predict-composition", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getCompositionModelStatus = () => API.get("/api/model/status");
