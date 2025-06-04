import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setErro("");
    try {
      const res = await axios.post("http://localhost:8000/login", { email, senha });
      onLogin(res.data);
      navigate("/");
    } catch (err) {
      setErro("Credenciais inválidas");
    }
  };

  return (
    <div style={{ maxWidth: 300, margin: "50px auto" }}>
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required className="form-control" />
        <input type="password" placeholder="Senha" value={senha} onChange={e => setSenha(e.target.value)} required className="form-control" />
        <button type="submit" className="btn btn-primary w-100 mt-2">Entrar</button>
      </form>
      {erro && <div className="alert alert-danger mt-2">{erro}</div>}
      <div className="mt-3 text-center">
        <Link to="/cadastro">Não tem cadastro? Cadastre-se</Link>
      </div>
    </div>
  );
}

export default Login;
