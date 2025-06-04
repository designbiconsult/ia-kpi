import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from './Navbar';
import IndicadoresSetor from './IndicadoresSetor';

const setores = ["Financeiro", "Comercial", "Produção"];

export default function Dashboard({ user, onLogout }) {
  const [setor, setSetor] = useState("Financeiro");
  const navigate = useNavigate();

  return (
    <div className="container">
      <Navbar onLogout={onLogout} />
      <h2>Bem-vindo, {user.nome}</h2>
      <div style={{display: "flex", gap: 16, marginBottom: 24}}>
        <button onClick={() => setSetor("Financeiro")}>Financeiro</button>
        <button onClick={() => setSetor("Comercial")}>Comercial</button>
        <button onClick={() => setSetor("Produção")}>Produção</button>
      </div>
      <IndicadoresSetor setor={setor} />
      <div style={{marginTop: 32}}>
        <button onClick={() => navigate("/config-conexao")}>Configurar Conexão</button>
        <button style={{marginLeft: 16}} onClick={() => navigate("/sincronizar-tabelas")}>Sincronizar Tabelas</button>
      </div>
    </div>
  );
}
