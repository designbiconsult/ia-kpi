import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from './Navbar';
import { api } from '../api';

export default function ConfigConexao({ user, onLogout }) {
  const [form, setForm] = useState({
    host: "",
    porta: "3306",
    usuario_banco: "",
    senha_banco: "",
    schema: "",
    intervalo_sync: 60
  });
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  const handleChange = e => setForm({...form, [e.target.name]: e.target.value});

  const handleSalvar = async e => {
    e.preventDefault();
    try {
      await api.put(`/usuarios/${user.id}/conexao`, form);
      setMsg("Configuração salva.");
      setTimeout(() => navigate("/dashboard"), 1000);
    } catch {
      setMsg("Erro ao salvar configuração.");
    }
  };

  return (
    <div className="container">
      <Navbar onLogout={onLogout} showBack={true} />
      <h2>Configurar conexão</h2>
      <form onSubmit={handleSalvar} className="form">
        <input name="host" placeholder="Host" value={form.host} onChange={handleChange} />
        <input name="porta" placeholder="Porta" value={form.porta} onChange={handleChange} />
        <input name="usuario_banco" placeholder="Usuário" value={form.usuario_banco} onChange={handleChange} />
        <input name="senha_banco" type="password" placeholder="Senha" value={form.senha_banco} onChange={handleChange} />
        <input name="schema" placeholder="Schema" value={form.schema} onChange={handleChange} />
        <input name="intervalo_sync" type="number" placeholder="Intervalo (min)" value={form.intervalo_sync} onChange={handleChange} />
        <button type="submit">Salvar</button>
      </form>
      {msg && <div className="info">{msg}</div>}
    </div>
  );
}
