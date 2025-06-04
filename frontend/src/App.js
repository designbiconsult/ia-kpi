import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Route, Routes, Navigate, useNavigate } from "react-router-dom";
import Login from "./Login";
import Cadastro from "./Cadastro";
import Dashboard from "./Dashboard";
import Conexao from "./Conexao";
import Sincronizar from "./Sincronizar";

function App() {
  const [usuario, setUsuario] = useState(() => {
    const u = localStorage.getItem("usuario");
    return u ? JSON.parse(u) : null;
  });

  const handleLogin = (user) => {
    setUsuario(user);
    localStorage.setItem("usuario", JSON.stringify(user));
  };

  const handleLogout = () => {
    setUsuario(null);
    localStorage.removeItem("usuario");
  };

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={usuario ? <Dashboard usuario={usuario} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />
        <Route path="/login" element={<Login onLogin={handleLogin} />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route
          path="/conexao"
          element={usuario ? <Conexao usuario={usuario} /> : <Navigate to="/login" />}
        />
        <Route
          path="/sincronizar"
          element={usuario ? <Sincronizar usuario={usuario} /> : <Navigate to="/login" />}
        />
      </Routes>
    </Router>
  );
}

export default App;
