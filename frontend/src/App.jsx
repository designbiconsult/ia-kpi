import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./Login";
import CadastroEmpresa from "./CadastroEmpresa";
import Dashboard from "./Dashboard";
import AdminDashboard from "./AdminDashboard";
import ConfigConexao from "./ConfigConexao";

export default function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) setUser(JSON.parse(stored));
  }, []);

  const handleLogin = (userObj) => {
    setUser(userObj);
    localStorage.setItem("user", JSON.stringify(userObj));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  const PrivateRoute = ({ children }) => (
    user ? children : <Navigate to="/login" />
  );

  const AdminRoute = ({ children }) =>
    user && user.perfil === "admin_geral" ? children : <Navigate to="/dashboard" />;

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={user ? <Navigate to="/dashboard" /> : <Navigate to="/login" />}
        />
        <Route
          path="/login"
          element={<Login onLogin={handleLogin} />}
        />
        <Route
          path="/cadastro_empresa"
          element={<CadastroEmpresa />}
        />
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Dashboard user={user} onLogout={handleLogout} />
            </PrivateRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <AdminDashboard user={user} onLogout={handleLogout} />
            </AdminRoute>
          }
        />
        <Route
          path="/conexao"
          element={
            <PrivateRoute>
              <ConfigConexao user={user} />
            </PrivateRoute>
          }
        />
        <Route
          path="*"
          element={user ? <Navigate to="/dashboard" /> : <Navigate to="/login" />}
        />
      </Routes>
    </BrowserRouter>
  );
}
