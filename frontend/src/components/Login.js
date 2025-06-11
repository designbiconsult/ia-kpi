import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '..\api';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setMsg("");
    try {
      const { data } = await api.post('/login', { email, senha });
      onLogin(data);
      navigate("/dashboard");
    } catch (err) {
      setMsg("Credenciais inválidas");
    }
  };

  return (
    <div className="login-box">
      <h2>Login IA KPI</h2>
      <form onSubmit={handleLogin}>
        <input placeholder="E-mail" value={email} onChange={e => setEmail(e.target.value)} />
        <input type="password" placeholder="Senha" value={senha} onChange={e => setSenha(e.target.value)} />
        <button type="submit">Entrar</button>
      </form>
      {msg && <div className="error">{msg}</div>}
      <p>
        Não tem conta? <span className="link" onClick={() => navigate("/cadastro")}>Cadastre-se</span>
      </p>
    </div>
  );
}
