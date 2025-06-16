import React, { useState, useEffect } from "react";
import {
  Box, Card, CardContent, Typography, TextField, Button,
  Alert, Stack, MenuItem
} from "@mui/material";
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

  useEffect(() => {
    async function fetchConexao() {
      try {
        const { data } = await axios.get(
          `http://localhost:8000/empresas/${user.empresa_id}`,
          {
            params: { email: user.email, senha: user.senha }
          }
        );
        setForm({
          tipo_banco: data.tipo_banco || "",
          host: data.host || "",
          porta: data.porta ? String(data.porta) : "",
          usuario_banco: data.usuario_banco || "",
          senha_banco: data.senha_banco || "",
          schema: data.schema || ""
        });
        setMsg("");
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
    setMsg("");
    setOk(false);
    try {
      // Monta o payload exatamente como o backend espera!
      const payload = {
        tipo_banco: form.tipo_banco,
        host: form.host,
        porta: Number(form.porta),  // Porta como número!
        usuario_banco: form.usuario_banco,
        senha_banco: form.senha_banco,
        schema: form.schema
      };
      await axios.put(
        `http://localhost:8000/empresas/${user.empresa_id}/conexao`,
        payload,
        {
          params: { email: user.email, senha: user.senha }
        }
      );
      setOk(true);
      setMsg("");
      setTimeout(() => navigate("/dashboard"), 1000);
    } catch (err) {
      let erroApi = err.response?.data?.detail || err.response?.data || "Erro ao salvar conexão.";
      if (Array.isArray(erroApi)) {
        erroApi = erroApi.map(e =>
          e.msg ? `${e.loc?.join(".") || ""}: ${e.msg}` : JSON.stringify(e)
        ).join(" | ");
      } else if (typeof erroApi === "object") {
        erroApi = JSON.stringify(erroApi);
      }
      setMsg(erroApi);
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
              <TextField
                select
                label="Tipo de Banco"
                name="tipo_banco"
                value={form.tipo_banco}
                onChange={handleChange}
                required
              >
                <MenuItem value="">Selecione...</MenuItem>
                <MenuItem value="mysql">MySQL / MariaDB</MenuItem>
                <MenuItem value="postgres">PostgreSQL</MenuItem>
                <MenuItem value="oracle">Oracle</MenuItem>
                <MenuItem value="mssql">SQL Server</MenuItem>
              </TextField>
              <TextField label="Host" name="host" value={form.host} onChange={handleChange} required />
              <TextField label="Porta" name="porta" value={form.porta} onChange={handleChange} required />
              <TextField label="Usuário do Banco" name="usuario_banco" value={form.usuario_banco} onChange={handleChange} required />
              <TextField label="Senha do Banco" type="password" name="senha_banco" value={form.senha_banco} onChange={handleChange} required />
              <TextField label="Schema/Banco" name="schema" value={form.schema} onChange={handleChange} required />
              {msg && <Alert severity="error">{msg}</Alert>}
              {ok && <Alert severity="success">Conexão salva com sucesso! Redirecionando...</Alert>}
              <Button variant="contained" color="primary" type="submit" sx={{ fontWeight: 700, background: "#0B2132", '&:hover': { background: "#06597a" } }} fullWidth>
                Salvar Conexão
              </Button>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
