import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from './Navbar';
import { api } from '../api';

export default function SincronizarTabelas({ onLogout }) {
  const [tabelas, setTabelas] = useState([]);
  const [selecionadas, setSelecionadas] = useState({});
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/tabelas').then(res => {
      const lista = res.data;
      setTabelas(lista);
      setSelecionadas(lista.reduce((acc, t) => ({...acc, [t]: false}), {}));
    });
  }, []);

  const handleCheck = t => setSelecionadas({...selecionadas, [t]: !selecionadas[t]});

  const handleSync = () => {
    // aqui você chamaria o endpoint de sincronismo, se existir, com as selecionadas
    setMsg("Sincronização simulada (implementar chamada real no backend)");
    setTimeout(() => navigate("/dashboard"), 1000);
  };

  return (
    <div className="container">
      <Navbar onLogout={onLogout} showBack={true} />
      <h2>Sincronizar Tabelas/Views</h2>
      <form>
        {tabelas.map(tb =>
          <div key={tb}>
            <input type="checkbox" checked={selecionadas[tb]} onChange={() => handleCheck(tb)} />
            {tb}
          </div>
        )}
      </form>
      <button style={{marginTop: 16}} onClick={handleSync}>Sincronizar selecionadas</button>
      {msg && <div className="info">{msg}</div>}
    </div>
  );
}
