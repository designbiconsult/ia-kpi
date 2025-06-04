import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { cadastrar } from './api';

function Cadastro() {
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro('');
    try {
      await cadastrar(nome, email, senha);
      navigate('/login');
    } catch {
      setErro('Erro ao cadastrar');
    }
  };

  return (
    <div className="container">
      <h2>Cadastro</h2>
      <form onSubmit={handleSubmit}>
        <input placeholder="Nome" value={nome} onChange={e => setNome(e.target.value)} />
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
        <input placeholder="Senha" type="password" value={senha} onChange={e => setSenha(e.target.value)} />
        <button type="submit">Cadastrar</button>
      </form>
      {erro && <div className="erro">{erro}</div>}
      <button onClick={() => navigate('/login')}>Voltar</button>
    </div>
  );
}

export default Cadastro;
