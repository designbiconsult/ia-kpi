import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Conexao({ usuario }) {
  const navigate = useNavigate();
  const [host, setHost] = useState("");
  const [porta, setPorta] = useState("");
  const [usuarioBanco, setUsuarioBanco] = useState("");
  const [senhaBanco, setSenhaBanco] = useState("");
  const [schema, setSchema] = useState("");
  const [msg, setMsg] = useState("");

  const handleSalvar = async (e) => {
    e.preventDefault();
    setMsg("");
    try {
      // *** Uso correto do id aqui ***
      await axios.put(`http://localhost:8000/usuarios/${usuario.id}/conexao`, {
        host, porta, usuario_banco: usuarioBanco, senha_banco: senhaBanco, schema
      });
      setMsg("Configuração salva!");
    } catch (err) {
      setMsg("Erro ao salvar: " + (err.response?.data?.detail || ""));
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "40px auto" }}>
      <button className="btn btn-light mb-2" onClick={() => navigate("/")}>← Voltar</button>
      <h3>Configuração da Conexão</h3>
      <form onSubmit={handleSalvar}>
        <input className="form-control" placeholder="Host" value={host} onChange={e => setHost(e.target.value)} />
        <input className="form-control" placeholder="Porta" value={porta} onChange={e => setPorta(e.target.value)} />
        <input className="form-control" placeholder="Usuário do banco" value={usuarioBanco} onChange={e => setUsuarioBanco(e.target.value)} />
        <input className="form-control" type="password" placeholder="Senha do banco" value={senhaBanco} onChange={e => setSenhaBanco(e.target.value)} />
        <input className="form-control" placeholder="Schema" value={schema} onChange={e => setSchema(e.target.value)} />
        <button type="submit" className="btn btn-primary w-100 mt-2">Salvar</button>
      </form>
      {msg && <div className="alert alert-info mt-2">{msg}</div>}
    </div>
  );
}

export default Conexao;
