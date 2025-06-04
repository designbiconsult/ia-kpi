import React, { useState } from "react";
import axios from "axios";

function PerguntaIA() {
  const usuario = JSON.parse(localStorage.getItem("usuario") || "{}");
  const [pergunta, setPergunta] = useState("");
  const [resposta, setResposta] = useState("");

  const handlePerguntar = async e => {
    e.preventDefault();
    setResposta("Consultando IA...");
    try {
      const resp = await axios.post("http://localhost:8000/pergunta_ia", null, {
        params: { usuario_id: usuario.id, pergunta }
      });
      setResposta(resp.data.resposta);
    } catch {
      setResposta("Erro ao consultar IA.");
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto" }}>
      <h2>Pergunte à IA</h2>
      <form onSubmit={handlePerguntar}>
        <input placeholder="Faça sua pergunta" value={pergunta} onChange={e => setPergunta(e.target.value)} style={{ width: "100%", marginBottom: 10 }} />
        <button type="submit">Perguntar</button>
      </form>
      <div style={{ marginTop: 24 }}>{resposta}</div>
    </div>
  );
}

export default PerguntaIA;
