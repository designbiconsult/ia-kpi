import React from "react";
import { useNavigate } from "react-router-dom";

function Dashboard({ usuario, onLogout }) {
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: 800, margin: "40px auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3>Bem-vindo, {usuario.nome}</h3>
        <button className="btn btn-secondary" onClick={onLogout}>Sair</button>
      </div>
      <hr />
      <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
        <button className="btn btn-info" onClick={() => navigate("/conexao")}>Configurar Conexão</button>
        <button className="btn btn-warning" onClick={() => navigate("/sincronizar")}>Sincronizar Tabelas</button>
      </div>
      <h4>Indicadores (exemplo)</h4>
      <div className="row">
        <div className="col">
          <div className="card text-bg-light mb-3"><div className="card-body">Financeiro<br />Receitas do mês<br />R$ --</div></div>
        </div>
        <div className="col">
          <div className="card text-bg-light mb-3"><div className="card-body">Financeiro<br />Despesas do mês<br />R$ --</div></div>
        </div>
        <div className="col">
          <div className="card text-bg-light mb-3"><div className="card-body">Financeiro<br />Saldo em caixa<br />R$ --</div></div>
        </div>
      </div>
      {/* Aqui adicione outros setores, cards, etc. */}
    </div>
  );
}

export default Dashboard;
