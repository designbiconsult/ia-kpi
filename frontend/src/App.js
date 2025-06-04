import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./Login";
import Cadastro from "./Cadastro";
import Dashboard from "./Dashboard";
import ConfigConexao from "./components/ConfigConexao";
import SincronizarTabelas from "./components/SincronizarTabelas";

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

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={!user ? <Navigate to="/login" /> : <Navigate to="/dashboard" />} />
        <Route path="/login" element={<Login onLogin={handleLogin} />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route
          path="/dashboard"
          element={user ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />
        <Route
          path="/conexao"
          element={user ? <ConfigConexao user={user} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />
        <Route
          path="/sincronizar"
          element={user ? <SincronizarTabelas user={user} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />
      </Routes>
    </BrowserRouter>
  );
}
