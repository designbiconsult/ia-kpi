import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8000",
});

// Exemplo de uso para buscar tabelas remotas com base no usuário logado
export async function buscarTabelasRemotas(usuario_id) {
  const resp = await api.get(`/tabelas-remotas?usuario_id=${usuario_id}`);
  return resp.data;
}
