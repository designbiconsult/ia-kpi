import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Cadastro from './components/Cadastro';
import Dashboard from './components/Dashboard';
import ConfigConexao from './components/ConfigConexao';
import SincronizarTabelas from './components/SincronizarTabelas';

function App() {
  const [user, setUser] = useState(JSON.parse(localStorage.getItem("usuario")) || null);

  const handleLogin = (usuario) => {
    setUser(usuario);
    localStorage.setItem("usuario", JSON.stringify(usuario));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("usuario");
  };

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login onLogin={handleLogin} />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route path="/dashboard" element={user ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
        <Route path="/config-conexao" element={user ? <ConfigConexao user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
        <Route path="/sincronizar-tabelas" element={user ? <SincronizarTabelas user={user} onLogout={handleLogout} /> : <Navigate to="/login" />} />
        <Route path="*" element={<Navigate to={user ? "/dashboard" : "/login"} />} />
      </Routes>
    </Router>
  );
}

export default App;
