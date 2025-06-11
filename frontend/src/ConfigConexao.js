import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { salvarConexao } from '.\api';

function ConfigConexao({ user }) {
  const [host, setHost] = useState('');
  const [porta, setPorta] = useState('');
  const [usuario_banco, setUsuarioBanco] = useState('');
  const [senha_banco, setSenhaBanco] = useState('');
  const [schema, setSchema] = useState('');
  const [ok, setOk] = useState('');
  const [erro, setErro] = useState('');
  const navigate = useNavigate();

  const handleSalvar = async (e) => {
    e.preventDefault();
    setErro('');
    setOk('');
    try {
      await salvarConexao({
        usuario_id: user.id,
        host, porta, usuario_banco, senha_banco, schema
      });
      setOk('Conexão salva!');
      setTimeout(() => navigate('/sync'), 800);
    } catch {
      setErro('Erro ao salvar conexão');
    }
  };

  return (
    <div className="container">
      <h2>Configurar Conexão</h2>
      <form onSubmit={handleSalvar}>
        <input placeholder="Host" value={host} onChange={e => setHost(e.target.value)} />
        <input placeholder="Porta" value={porta} onChange={e => setPorta(e.target.value)} />
        <input placeholder="Usuário" value={usuario_banco} onChange={e => setUsuarioBanco(e.target.value)} />
        <input placeholder="Senha" type="password" value={senha_banco} onChange={e => setSenhaBanco(e.target.value)} />
        <input placeholder="Schema" value={schema} onChange={e => setSchema(e.target.value)} />
        <button type="submit">Salvar</button>
      </form>
      {ok && <div className="ok">{ok}</div>}
      {erro && <div className="erro">{erro}</div>}
    </div>
  );
}

export default ConfigConexao;
