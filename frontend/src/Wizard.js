import React, { useState } from "react";
import axios from "axios";

function Wizard() {
  const usuario = JSON.parse(localStorage.getItem("usuario") || "{}");
  const [setor, setSetor] = useState("Financeiro");
  const [nome, setNome] = useState("");
  const [mapeamento, setMapeamento] = useState("");
  const [msg, setMsg] = useState("");

  const handleSalvar = async e => {
    e.preventDefault();
    try {
      await axios.post(`http://localhost:8000/indicadores/${usuario.id}/${setor}?nome=${nome}&mapeamento=${mapeamento}`);
      setMsg("Indicador salvo!");
    } catch {
      setMsg("Erro ao salvar.");
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "0 auto" }}>
      <h2>Wizard de Indicador</h2>
      <form onSubmit={handleSalvar}>
        <input placeholder="Setor" value={setor} onChange={e => setSetor(e.target.value)} style={{ width: "100%", marginBottom: 10 }} />
        <input placeholder="Nome do indicador" value={nome} onChange={e => setNome(e.target.value)} style={{ width: "100%", marginBottom: 10 }} />
        <input placeholder="Mapeamento (ex: tabela.coluna...)" value={mapeamento} onChange={e => setMapeamento(e.target.value)} style={{ width: "100%", marginBottom: 10 }} />
        <button type="submit" style={{ width: "100%" }}>Salvar</button>
      </form>
      <div style={{ marginTop: 16 }}>{msg}</div>
    </div>
  );
}

export default Wizard;
