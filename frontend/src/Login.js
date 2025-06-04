import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from './api';

function Login({ setUser }) {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro('');
    try {
      const res = await login(email, senha);
      localStorage.setItem("user", JSON.stringify(res.data));
      setUser(res.data);
      navigate('/');
    } catch {
      setErro('Credenciais inválidas');
    }
  };

  return (
    <div className="container">
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
        <input placeholder="Senha" type="password" value={senha} onChange={e => setSenha(e.target.value)} />
        <button type="submit">Entrar</button>
      </form>
      {erro && <div className="erro">{erro}</div>}
      <button onClick={() => navigate('/cadastro')}>Cadastrar</button>
    </div>
  );
}

export default Login;
