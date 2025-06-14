import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8000",
});

export async function buscarUsuario(id) {
  const resp = await api.get(`/usuarios/${id}`);
  return resp.data;
}

export async function buscarTabelasRemotas(usuario_id) {
  const resp = await api.get("/tabelas-remotas", { params: { usuario_id } });
  return resp.data;
}
