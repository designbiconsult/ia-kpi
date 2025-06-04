import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Login({ setLogado }) {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async e => {
    e.preventDefault();
    setErro("");
    try {
      const resp = await axios.post("http://localhost:8000/usuarios/login", { email, senha });
      localStorage.setItem("usuario", JSON.stringify(resp.data));
      setLogado(true);
      navigate("/indicators");
    } catch (err) {
      setErro("Usuário ou senha inválidos.");
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "50px auto" }}>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} style={{ width: "100%", marginBottom: 12 }} />
        <input type="password" placeholder="Senha" value={senha} onChange={e => setSenha(e.target.value)} style={{ width: "100%", marginBottom: 12 }} />
        <button type="submit" style={{ width: "100%" }}>Entrar</button>
      </form>
      {erro && <div style={{ color: "red", marginTop: 12 }}>{erro}</div>}
    </div>
  );
}

export default Login;
