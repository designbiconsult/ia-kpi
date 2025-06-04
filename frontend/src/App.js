import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Login from './Login';
import Cadastro from './Cadastro';
import ConfigConexao from './ConfigConexao';
import SyncTabelas from './SyncTabelas';
import Dashboard from './Dashboard';
import Diagram from './Diagram';
import IndicadorWizard from './IndicadorWizard';
import './styles/main.css';

function App() {
  const [user, setUser] = React.useState(JSON.parse(localStorage.getItem("user")) || null);

  return (
    <Router>
      <Routes>
        <Route path="/" element={user ? <Dashboard user={user} /> : <Navigate to="/login" />} />
        <Route path="/login" element={<Login setUser={setUser} />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route path="/config" element={user ? <ConfigConexao user={user} /> : <Navigate to="/login" />} />
        <Route path="/sync" element={user ? <SyncTabelas user={user} /> : <Navigate to="/login" />} />
        <Route path="/diagram" element={user ? <Diagram user={user} /> : <Navigate to="/login" />} />
        <Route path="/wizard" element={user ? <IndicadorWizard user={user} /> : <Navigate to="/login" />} />
        {/* 404 */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}
export default App;
