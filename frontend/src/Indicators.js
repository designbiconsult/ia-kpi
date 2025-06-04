import React, { useState, useEffect } from "react";
import axios from "axios";

const SETORES = ["Financeiro", "Comercial", "Produção"];

function Indicators() {
  const usuario = JSON.parse(localStorage.getItem("usuario") || "{}");
  const [setor, setSetor] = useState(SETORES[0]);
  const [indicadores, setIndicadores] = useState([]);

  useEffect(() => {
    axios.get(`http://localhost:8000/indicadores/${usuario.id}/${setor}`).then(r => setIndicadores(r.data));
  }, [setor, usuario.id]);

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <h2>Indicadores Básicos</h2>
      <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        {SETORES.map(s => (
          <button key={s} onClick={() => setSetor(s)} style={{ background: setor === s ? "#0a7" : "#ddd" }}>{s}</button>
        ))}
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Valor/Mapeamento</th>
          </tr>
        </thead>
        <tbody>
          {indicadores.map(ind => (
            <tr key={ind.id}>
              <td>{ind.nome}</td>
              <td>{ind.mapeamento}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Indicators;
