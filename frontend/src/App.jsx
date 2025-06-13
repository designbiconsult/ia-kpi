import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./Login";
import CadastroEmpresa from "./CadastroEmpresa";
import Dashboard from "./Dashboard";
import AdminDashboard from "./AdminDashboard"; // (exemplo, crie esse componente)
import axios from "axios";

export default function App() {
  const [user, setUser] = useState(null);

  // Mantém login após refresh
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

  // Protege rotas privadas
  const PrivateRoute = ({ children }) => (
    user ? children : <Navigate to="/login" />
  );

  // Protege rotas só para admin_geral
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

        {/* Rota para dashboard (visível para qualquer usuário autenticado) */}
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Dashboard user={user} onLogout={handleLogout} />
            </PrivateRoute>
          }
        />

        {/* Rota para admin dashboard (apenas para admin_geral) */}
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <AdminDashboard user={user} onLogout={handleLogout} />
            </AdminRoute>
          }
        />

        {/* Se acessar qualquer rota desconhecida, redireciona para dashboard ou login */}
        <Route
          path="*"
          element={user ? <Navigate to="/dashboard" /> : <Navigate to="/login" />}
        />
      </Routes>
    </BrowserRouter>
  );
}
