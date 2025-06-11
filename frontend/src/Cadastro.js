import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from ".api";

export default function Cadastro() {
  const [form, setForm] = useState({ nome: "", email: "", senha: "" });
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      await api.post("/usuarios", form);
      setMsg("Cadastro realizado com sucesso. Faça login!");
      setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      if (err?.response?.data?.detail) setMsg(err.response.data.detail);
      else setMsg("Erro ao cadastrar.");
    }
  };

  return (
    <div className="container">
      <h2>Cadastro</h2>
      <form onSubmit={handleSubmit} className="form">
        <input name="nome" placeholder="Nome completo" value={form.nome} onChange={handleChange} />
        <input name="email" placeholder="Email" value={form.email} onChange={handleChange} />
        <input name="senha" type="password" placeholder="Senha" value={form.senha} onChange={handleChange} />
        <button type="submit">Cadastrar</button>
      </form>
      <button onClick={() => navigate("/login")}>Voltar ao Login</button>
      {msg && <div className="info">{msg}</div>}
    </div>
  );
}
