import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";

function Cadastro() {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");
  const navigate = useNavigate();

  const handleCadastro = async (e) => {
    e.preventDefault();
    setErro(""); setSucesso("");
    try {
      await axios.post("http://localhost:8000/usuarios", { nome, email, senha });
      setSucesso("Cadastro realizado com sucesso!");
      setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      setErro(err.response?.data?.detail || "Erro ao cadastrar");
    }
  };

  return (
    <div style={{ maxWidth: 300, margin: "50px auto" }}>
      <h2>Cadastro</h2>
      <form onSubmit={handleCadastro}>
        <input type="text" placeholder="Nome" value={nome} onChange={e => setNome(e.target.value)} required className="form-control" />
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required className="form-control" />
        <input type="password" placeholder="Senha" value={senha} onChange={e => setSenha(e.target.value)} required className="form-control" />
        <button type="submit" className="btn btn-success w-100 mt-2">Cadastrar</button>
      </form>
      {erro && <div className="alert alert-danger mt-2">{erro}</div>}
      {sucesso && <div className="alert alert-success mt-2">{sucesso}</div>}
      <div className="mt-3 text-center">
        <Link to="/login">Já tem cadastro? Login</Link>
      </div>
    </div>
  );
}

export default Cadastro;
