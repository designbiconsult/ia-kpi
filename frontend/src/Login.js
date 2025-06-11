import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from ".api";

export default function Login({ onLogin }) {
  const [form, setForm] = useState({ email: "", senha: "" });
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      const { data } = await api.post("/login", form);
      onLogin(data);
      navigate("/dashboard");
    } catch {
      setMsg("Credenciais inválidas.");
    }
  };

  return (
    <div className="container">
      <h2>Login</h2>
      <form onSubmit={handleSubmit} className="form">
        <input name="email" placeholder="Email" value={form.email} onChange={handleChange} />
        <input name="senha" type="password" placeholder="Senha" value={form.senha} onChange={handleChange} />
        <button type="submit">Entrar</button>
      </form>
      <button onClick={() => navigate("/cadastro")}>Cadastre-se</button>
      {msg && <div className="error">{msg}</div>}
    </div>
  );
}
