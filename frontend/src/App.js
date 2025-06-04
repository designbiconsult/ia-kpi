import React from "react";
import { BrowserRouter as Router, Route, Routes, Navigate, Link } from "react-router-dom";
import Login from "./Login";
import Cadastro from "./Cadastro";
import Sync from "./Sync";
import Diagram from "./Diagram";
import Indicators from "./Indicators";
import Wizard from "./Wizard";
import PerguntaIA from "./PerguntaIA";

function App() {
  // Exemplo: controle simples de autenticação via localStorage
  const [logado, setLogado] = React.useState(!!localStorage.getItem("usuario"));

  function handleLogout() {
    localStorage.removeItem("usuario");
    setLogado(false);
  }

  return (
    <Router>
      <nav style={{ background: "#222", padding: 16, color: "#fff", marginBottom: 24 }}>
        <Link to="/" style={{ color: "#fff", marginRight: 20, textDecoration: "none" }}>🏠 Home</Link>
        {logado && (
          <>
            <Link to="/sync" style={{ color: "#fff", marginRight: 20 }}>Sincronizar</Link>
            <Link to="/diagram" style={{ color: "#fff", marginRight: 20 }}>Relacionamentos</Link>
            <Link to="/indicators" style={{ color: "#fff", marginRight: 20 }}>Indicadores</Link>
            <Link to="/wizard" style={{ color: "#fff", marginRight: 20 }}>Wizard</Link>
            <Link to="/pergunta" style={{ color: "#fff", marginRight: 20 }}>Pergunta IA</Link>
            <button onClick={handleLogout} style={{ marginLeft: 20, background: "#d33", color: "#fff", border: 0, padding: "4px 12px", borderRadius: 4 }}>Sair</button>
          </>
        )}
        {!logado && (
          <>
            <Link to="/login" style={{ color: "#fff", marginRight: 20 }}>Login</Link>
            <Link to="/cadastro" style={{ color: "#fff", marginRight: 20 }}>Cadastro</Link>
          </>
        )}
      </nav>
      <Routes>
        <Route path="/login" element={<Login setLogado={setLogado} />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route path="/sync" element={logado ? <Sync /> : <Navigate to="/login" />} />
        <Route path="/diagram" element={logado ? <Diagram /> : <Navigate to="/login" />} />
        <Route path="/indicators" element={logado ? <Indicators /> : <Navigate to="/login" />} />
        <Route path="/wizard" element={logado ? <Wizard /> : <Navigate to="/login" />} />
        <Route path="/pergunta" element={logado ? <PerguntaIA /> : <Navigate to="/login" />} />
        <Route path="/" element={logado ? <Indicators /> : <Navigate to="/login" />} />
        <Route path="*" element={<div>Página não encontrada.</div>} />
      </Routes>
    </Router>
  );
}

export default App;
