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
import { IconButton, Toolbar, AppBar, Box, Typography, Button } from "@mui/material";
import RelacionamentosVisual from "./RelacionamentosVisual";

const drawerWidth = 230;

export default function App() {
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Abre menu lateral automaticamente após login
  useEffect(() => {
    if (user) setSidebarOpen(true);
  }, [user]);

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
      <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: "#f8fafd" }}>
        {user && <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />}
        
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            transition: 'margin 0.2s',
            marginLeft: user && sidebarOpen ? `${drawerWidth}px` : 0,
            minHeight: '100vh',
            bgcolor: "#f8fafd"
          }}
        >
          {/* Topbar fixa */}
          {user && (
            <AppBar
              position="fixed"
              elevation={0}
              sx={{
                width: user && sidebarOpen ? `calc(100% - ${drawerWidth}px)` : '100%',
                ml: user && sidebarOpen ? `${drawerWidth}px` : 0,
                bgcolor: "#e6f0fa",
                color: "#0B2132",
                boxShadow: "none"
              }}
            >
              <Toolbar>
                {!sidebarOpen && (
                  <IconButton
                    color="inherit"
                    edge="start"
                    onClick={() => setSidebarOpen(true)}
                    sx={{ mr: 2 }}
                  >
                    <MenuIcon />
                  </IconButton>
                )}
                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                  IA-KPI
                </Typography>
                <Typography variant="body1" sx={{ mr: 2 }}>
                  {user?.nome}
                </Typography>
                <Button color="inherit" onClick={handleLogout}>Sair</Button>
              </Toolbar>
            </AppBar>
          )}
          {/* Espaço para não cobrir pelo AppBar */}
          {user && <Toolbar />}
          
          {/* Rotas */}
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
              path="/relacionamentos-visual"
              element={
                <PrivateRoute>
                  <RelacionamentosVisual user={user} />
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
