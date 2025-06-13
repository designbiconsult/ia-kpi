import React, { useState, useEffect } from "react";
import { Box, Card, CardContent, Typography, TextField, Button, Alert, Stack } from "@mui/material";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function ConfigConexao({ user }) {
  const [form, setForm] = useState({
    tipo_banco: "",
    host: "",
    porta: "",
    usuario_banco: "",
    senha_banco: "",
    schema: ""
  });
  const [msg, setMsg] = useState("");
  const [ok, setOk] = useState(false);
  const [carregando, setCarregando] = useState(true);
  const navigate = useNavigate();

  // Busca os dados atuais da empresa ao carregar
  useEffect(() => {
    async function fetchConexao() {
      try {
        // Precisa autenticar enviando email/senha do user no body (como no backend)
        const { data } = await axios.get(
          `http://localhost:8000/empresas/${user.empresa_id}`,
          {
            data: { email: user.email, senha: user.senha }
          }
        );
        setForm({
          tipo_banco: data.tipo_banco || "",
          host: data.host || "",
          porta: data.porta || "",
          usuario_banco: data.usuario_banco || "",
          senha_banco: data.senha_banco || "",
          schema: data.schema || ""
        });
      } catch (err) {
        setMsg("Não foi possível carregar a conexão.");
      } finally {
        setCarregando(false);
      }
    }
    if (user?.empresa_id) fetchConexao();
    // eslint-disable-next-line
  }, [user]);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    setMsg(""); setOk(false);
    try {
      await axios.put(
        `http://localhost:8000/empresas/${user.empresa_id}/conexao`,
        { ...form, email: user.email, senha: user.senha }
      );
      setOk(true);
      setMsg("");
    } catch (err) {
      setMsg(err.response?.data?.detail || "Erro ao salvar conexão.");
      setOk(false);
    }
  };

  if (carregando) {
    return (
      <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center">
        <Typography>Carregando dados da conexão...</Typography>
      </Box>
    );
  }

  return (
    <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center" sx={{ background: 'linear-gradient(120deg, #f8fafd 60%, #e4f3fa 100%)' }}>
      <Card sx={{ minWidth: 350, maxWidth: 480, px: 3, py: 4, borderRadius: 4, boxShadow: '0 4px 32px #6fc7ea18' }}>
        <CardContent>
          <Stack spacing={2} alignItems="center" mb={2}>
            <Typography variant="h5" fontWeight={700} color="#0B2132">
              Configuração de Conexão
            </Typography>
            <Typography color="text.secondary" fontSize={15}>
              Defina ou edite as informações de acesso ao banco de dados da empresa.
            </Typography>
          </Stack>
          <form onSubmit={handleSubmit} autoComplete="off">
            <Stack spacing={2}>
              <TextField label="Tipo de Banco" name="tipo_banco" value={form.tipo_banco} onChange={handleChange} required />
              <TextField label="Host" name="host" value={form.host} onChange={handleChange} required />
              <TextField label="Porta" name="porta" value={form.porta} onChange={handleChange} required />
              <TextField label="Usuário do Banco" name="usuario_banco" value={form.usuario_banco} onChange={handleChange} required />
              <TextField label="Senha do Banco" name="senha_banco" value={form.senha_banco} onChange={handleChange} required />
              <TextField label="Schema/Banco" name="schema" value={form.schema} onChange={handleChange} required />
              {msg && <Alert severity="error">{msg}</Alert>}
              {ok && <Alert severity="success">Conexão salva com sucesso!</Alert>}
              <Button variant="contained" color="primary" type="submit" sx={{ fontWeight: 700, background: "#0B2132", '&:hover': { background: "#06597a" } }} fullWidth>
                Salvar Conexão
              </Button>
              <Button onClick={() => navigate("/dashboard")} variant="text" color="secondary" fullWidth>
                Voltar ao Dashboard
              </Button>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
