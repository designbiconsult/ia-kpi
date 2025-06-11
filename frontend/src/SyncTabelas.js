import React, { useState, useEffect } from 'react';
import { listarTabelas, sincronizarTabelas } from '.api';
import { useNavigate } from 'react-router-dom';

function SyncTabelas({ user }) {
  const [tabelas, setTabelas] = useState([]);
  const [selecionadas, setSelecionadas] = useState([]);
  const [ok, setOk] = useState('');
  const [erro, setErro] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    listarTabelas().then(res => setTabelas(res.data));
  }, []);

  const handleSync = async () => {
    setErro('');
    setOk('');
    if (!selecionadas.length) {
      setErro('Selecione ao menos uma tabela');
      return;
    }
    try {
      await sincronizarTabelas(selecionadas);
      setOk('Sincronização realizada!');
      setTimeout(() => navigate('/'), 800);
    } catch {
      setErro('Erro ao sincronizar');
    }
  };

  return (
    <div className="container">
      <h2>Selecionar Tabelas/Views</h2>
      {tabelas.map(tb => (
        <div key={tb}>
          <label>
            <input
              type="checkbox"
              value={tb}
              checked={selecionadas.includes(tb)}
              onChange={e => {
                if (e.target.checked) setSelecionadas([...selecionadas, tb]);
                else setSelecionadas(selecionadas.filter(t => t !== tb));
              }}
            />
            {tb}
          </label>
        </div>
      ))}
      <button onClick={handleSync}>Sincronizar</button>
      {ok && <div className="ok">{ok}</div>}
      {erro && <div className="erro">{erro}</div>}
    </div>
  );
}

export default SyncTabelas;
