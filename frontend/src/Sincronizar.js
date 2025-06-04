import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Sincronizar({ usuario }) {
  const navigate = useNavigate();
  const [tabelas, setTabelas] = useState([]);
  const [selecionadas, setSelecionadas] = useState([]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    // Simula busca de tabelas. Troque o endpoint conforme sua API real.
    axios.get("http://localhost:8000/tabelas")
      .then(res => setTabelas(res.data))
      .catch(() => setTabelas([]));
  }, []);

  const handleSync = () => {
    setMsg("Sincronização simulada! (implemente a chamada real aqui)");
    // Aqui você chamaria o endpoint de sincronismo
  };

  return (
    <div style={{ maxWidth: 500, margin: "40px auto" }}>
      <button className="btn btn-light mb-2" onClick={() => navigate("/")}>← Voltar</button>
      <h3>Sincronizar Tabelas</h3>
      <ul className="list-group mb-3">
        {tabelas.map(tb => (
          <li key={tb} className="list-group-item">
            <input
              type="checkbox"
              checked={selecionadas.includes(tb)}
              onChange={() =>
                setSelecionadas(selecionadas.includes(tb)
                  ? selecionadas.filter(x => x !== tb)
                  : [...selecionadas, tb]
                )
              }
            />{" "}
            {tb}
          </li>
        ))}
      </ul>
      <button className="btn btn-success" onClick={handleSync}>Sincronizar Selecionadas</button>
      {msg && <div className="alert alert-info mt-2">{msg}</div>}
    </div>
  );
}

export default Sincronizar;
