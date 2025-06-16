import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./Login";
import CadastroEmpresa from "./CadastroEmpresa";
import Dashboard from "./Dashboard";
import AdminDashboard from "./AdminDashboard";
import ConfigConexao from "./ConfigConexao";
import SincronizarTabelas from "./SincronizarTabelas";
import Relacionamentos from "./Relacionamentos";
import Sidebar from "./Sidebar";
import MenuIcon from '@mui/icons-material/Menu';
import { IconButton, Toolbar, Box } from "@mui/material";

export default function App() {
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) setUser(JSON.parse(stored));
  }, []);

  React.useEffect(() => {
  if (user) setSidebarOpen(true);
}, [user]);

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
      <Box sx={{ display: 'flex' }}>
        {user && <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />}
        <Box component="main" sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: "#f8fafd" }}>
          {/* Top bar só mostra o botão de menu se estiver logado */}
          {user && (
            <Toolbar sx={{ bgcolor: "#e6f0fa" }}>
              <IconButton onClick={() => setSidebarOpen(true)} sx={{ mr: 2 }}>
                <MenuIcon />
              </IconButton>
              {/* Aqui você pode colocar o nome do usuário, logo, etc */}
            </Toolbar>
          )}
          <Routes>
            <Route
              path="/sincronizar"
              element={
                <PrivateRoute>
                  <SincronizarTabelas user={user} onLogout={handleLogout} />
                </PrivateRoute>
              }
            />
            <Route
              path="/relacionamentos"
              element={
                <PrivateRoute>
                  <Relacionamentos user={user} />
                </PrivateRoute>
              }
            />
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
        </Box>
      </Box>
    </BrowserRouter>
  );
}
