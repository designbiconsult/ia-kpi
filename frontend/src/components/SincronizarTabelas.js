import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from './Navbar';
import { api } from '../api';

export default function SincronizarTabelas({ user, onLogout }) {
  const [tabelas, setTabelas] = useState([]);
  const [selecionadas, setSelecionadas] = useState([]);
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchTabelas() {
      try {
        const { data } = await api.get(`/tabelas-remotas`);
        setTabelas(data);
      } catch {
        setMsg("Erro ao buscar tabelas remotas.");
      }
    }
    fetchTabelas();
  }, []);

  const handleChange = (tb) => {
    setSelecionadas(selecionadas.includes(tb)
      ? selecionadas.filter(t => t !== tb)
      : [...selecionadas, tb]
    );
  };

  const handleSync = async () => {
    try {
      await api.post(`/sincronizar`, { tabelas: selecionadas, usuario_id: user.id });
      setMsg("Sincronização concluída!");
    } catch {
      setMsg("Erro ao sincronizar.");
    }
  };

  return (
    <div className="container">
      <Navbar onLogout={onLogout} showBack={true} />
      <h2>Sincronizar Tabelas/Views</h2>
      {tabelas.length === 0 && <div>Nenhuma tabela remota encontrada.</div>}
      {tabelas.map(tb => (
        <div key={tb}>
          <input type="checkbox" checked={selecionadas.includes(tb)} onChange={() => handleChange(tb)} />
          {tb}
        </div>
      ))}
      <button onClick={handleSync} disabled={selecionadas.length === 0}>Sincronizar selecionadas</button>
      <button onClick={() => navigate("/dashboard")}>Voltar</button>
      {msg && <div className="info">{msg}</div>}
    </div>
  );
}
