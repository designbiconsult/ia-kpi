import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const login = (email, senha) =>
  axios.post(`${API_URL}/login`, { email, senha });

export const cadastrar = (nome, email, senha) =>
  axios.post(`${API_URL}/cadastro`, { nome, email, senha });

export const salvarConexao = (dados) =>
  axios.post(`${API_URL}/conexao`, dados);

export const listarTabelas = () =>
  axios.get(`${API_URL}/tabelas`);

export const listarColunas = (tabela) =>
  axios.get(`${API_URL}/colunas/${tabela}`);

export const sincronizarTabelas = (tabelas) =>
  axios.post(`${API_URL}/sincronizar`, { tabelas });

export const listarRelacionamentos = () =>
  axios.get(`${API_URL}/relacionamentos`);

export const criarRelacionamento = (rel) =>
  axios.post(`${API_URL}/relacionamentos`, rel);

export const deletarRelacionamento = (rel_id) =>
  axios.delete(`${API_URL}/relacionamentos/${rel_id}`);

export const listarIndicadores = (setor) =>
  axios.get(`${API_URL}/indicadores?setor=${setor}`);

export const criarIndicador = (indicador) =>
  axios.post(`${API_URL}/indicadores`, indicador);

export const perguntarIA = (pergunta) =>
  axios.post(`${API_URL}/perguntar_ia`, { pergunta });

