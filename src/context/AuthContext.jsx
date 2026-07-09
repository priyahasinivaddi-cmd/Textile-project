/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState } from "react";

const AuthContext = createContext();

// Provider
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(
    JSON.parse(localStorage.getItem("user")) || null
  );

  const login = (data) => {
    localStorage.setItem("user", JSON.stringify(data));
    setUser(data);
  };

  const logout = () => {
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook
export const useAuth = () => {
  return useContext(AuthContext);
};
