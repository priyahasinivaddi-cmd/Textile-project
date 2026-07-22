import API from "./api";

/**
 * Sends a textile image file to the backend to be analyzed by the AI pipeline.
 * @param {File} file The image file to analyze
 * @param {number} sensitivity The detection sensitivity (0.0 to 1.0)
 * @returns {Promise} Axios promise with the analysis results
 */
export const analyzeImage = (file, sensitivity = 0.5) => {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("sensitivity", sensitivity);

  return API.post("/pipeline/analyze", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};
