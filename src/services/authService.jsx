import API from "./api";

// ✅ Register
export const registerUser = (data) => {
  return API.post("/user/register", data);
};

// ✅ Login
export const loginUser = (data) => {
  const formData = new URLSearchParams();
  formData.append("username", data.email); // 👈 MUST be 'username'
  formData.append("password", data.password);

  return API.post("/user/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
};