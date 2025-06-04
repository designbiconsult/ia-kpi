import React, { useState } from "react";
import axios from "axios";

function Sync() {
  const [msg, setMsg] = useState("");
  const usuario = JSON.parse(localStorage.getItem("usuario") || "{}");

  const handleSync = async () => {
    setMsg("Sincronizando...");
    try {
      await axios.post(`http://localhost:8000/sync?usuario_id=${usuario.id}`);
      setMsg("Sincronização concluída!");
    } catch (err) {
      setMsg("Erro na sincronização.");
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "40px auto" }}>
      <h2>Sincronização de Dados</h2>
      <p>Atualize as tabelas do seu banco de dados (MySQL → SQLite).</p>
      <button onClick={handleSync}>Sincronizar Agora</button>
      <div style={{ marginTop: 24 }}>{msg}</div>
    </div>
  );
}

export default Sync;
