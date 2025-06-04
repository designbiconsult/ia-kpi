import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Cadastro() {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async e => {
    e.preventDefault();
    setErro("");
    setSucesso("");
    try {
      await axios.post("http://localhost:8000/usuarios/cadastro", { nome, email, senha });
      setSucesso("Cadastro realizado! Faça login.");
      setTimeout(() => navigate("/login"), 1000);
    } catch (err) {
      setErro("Erro ao cadastrar. Email já usado?");
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "50px auto" }}>
      <h2>Cadastro</h2>
      <form onSubmit={handleSubmit}>
        <input placeholder="Nome" value={nome} onChange={e => setNome(e.target.value)} style={{ width: "100%", marginBottom: 12 }} />
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} style={{ width: "100%", marginBottom: 12 }} />
        <input type="password" placeholder="Senha" value={senha} onChange={e => setSenha(e.target.value)} style={{ width: "100%", marginBottom: 12 }} />
        <button type="submit" style={{ width: "100%" }}>Cadastrar</button>
      </form>
      {erro && <div style={{ color: "red", marginTop: 12 }}>{erro}</div>}
      {sucesso && <div style={{ color: "green", marginTop: 12 }}>{sucesso}</div>}
    </div>
  );
}

export default Cadastro;
