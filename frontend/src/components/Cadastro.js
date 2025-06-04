import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

export default function Cadastro() {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  const handleCadastro = async (e) => {
    e.preventDefault();
    setMsg("");
    try {
      await api.post('/usuarios', { nome, email, senha });
      setMsg("Cadastro realizado! Faça login.");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setMsg("Erro no cadastro (e-mail pode já existir).");
    }
  };

  return (
    <div className="login-box">
      <h2>Cadastro</h2>
      <form onSubmit={handleCadastro}>
        <input placeholder="Nome completo" value={nome} onChange={e => setNome(e.target.value)} />
        <input placeholder="E-mail" value={email} onChange={e => setEmail(e.target.value)} />
        <input type="password" placeholder="Senha" value={senha} onChange={e => setSenha(e.target.value)} />
        <button type="submit">Cadastrar</button>
      </form>
      {msg && <div className="error">{msg}</div>}
      <p>
        Já tem conta? <span className="link" onClick={() => navigate("/login")}>Entrar</span>
      </p>
    </div>
  );
}
