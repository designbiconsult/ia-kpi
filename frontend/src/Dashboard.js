import React, { useState, useEffect } from 'react';
import SetorTabs from './components/SetorTabs';
import IndicadorCard from './components/IndicadorCard';
import { listarIndicadores } from './api';
import { useNavigate } from 'react-router-dom';

const setores = ["Financeiro", "Comercial", "Produção"];

function Dashboard({ user }) {
  const [setor, setSetor] = useState(setores[0]);
  const [indicadores, setIndicadores] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    listarIndicadores(setor).then(res => setIndicadores(res.data));
  }, [setor]);

  return (
    <div className="container">
      <h2>Dashboard de Indicadores</h2>
      <SetorTabs setores={setores} setor={setor} setSetor={setSetor} />
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {indicadores.map(ind => (
          <IndicadorCard key={ind.id} indicador={ind} />
        ))}
        <button onClick={() => navigate('/wizard')}>Novo Indicador</button>
      </div>
      <button onClick={() => navigate('/diagram')}>Relacionamentos (drag & drop)</button>
      <button onClick={() => navigate('/config')}>Configurar Conexão</button>
      <button onClick={() => navigate('/sync')}>Sincronizar Tabelas</button>
    </div>
  );
}

export default Dashboard;
