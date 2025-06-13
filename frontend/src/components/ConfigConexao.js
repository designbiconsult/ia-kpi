import React, { useState, useEffect } from "react";
import {
  Box, Card, CardContent, Typography, TextField, Button, Alert, Stack, Avatar
} from "@mui/material";
import { api } from "../api";
import { useNavigate } from "react-router-dom";

export default function ConfigConexao({ user, onLogout }) {
  const [form, setForm] = useState({
    host: "",
    porta: "",
    usuario_banco: "",
    senha_banco: "",
    schema: ""
  });
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Preenche com dados existentes, se houver
  useEffect(() => {
    if (user) {
      setForm({
        host: user.host || "",
        porta: user.porta || "",
        usuario_banco: user.usuario_banco || "",
        senha_banco: user.senha_banco || "",
        schema: user.schema || ""
      });
    }
  }, [user]);

  const handleChange = e =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSalvar = async e => {
    e.preventDefault();
    setErro(""); setSucesso("");
    setLoading(true);

    try {
      await api.put(`/usuarios/${user.id}/conexao`, form);
      setSucesso("Conexão salva com sucesso!");
    } catch (err) {
      setErro("Erro ao salvar conexão. Verifique os dados e tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      minHeight="100vh"
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(120deg, #f8fafd 60%, #e4f3fa 100%)'
      }}
    >
      <Card sx={{
        minWidth: 350,
        maxWidth: 480,
        px: 4, py: 5,
        borderRadius: 4,
        boxShadow: '0 4px 32px #6fc7ea18'
      }}>
        <CardContent>
          <Stack direction="row" spacing={2} alignItems="center" mb={3}>
            <Avatar sx={{ width: 48, height: 48, bgcolor: "#2284a1" }}>🔌</Avatar>
            <Typography variant="h5" fontWeight={700} color="#2284a1">
              Configurar Conexão MySQL
            </Typography>
          </Stack>
          <form onSubmit={handleSalvar} autoComplete="off">
            <Stack spacing={2}>
              <TextField
                label="Host"
                name="host"
                value={form.host}
                onChange={handleChange}
                required
                fullWidth
              />
              <TextField
                label="Porta"
                name="porta"
                value={form.porta}
                onChange={handleChange}
                required
                fullWidth
              />
              <TextField
                label="Usuário do Banco"
                name="usuario_banco"
                value={form.usuario_banco}
                onChange={handleChange}
                required
                fullWidth
              />
              <TextField
                label="Senha do Banco"
                name="senha_banco"
                type="password"
                value={form.senha_banco}
                onChange={handleChange}
                required
                fullWidth
              />
              <TextField
                label="Schema"
                name="schema"
                value={form.schema}
                onChange={handleChange}
                required
                fullWidth
              />
              {erro && <Alert severity="error">{erro}</Alert>}
              {sucesso && <Alert severity="success">{sucesso}</Alert>}
              <Button
                type="submit"
                variant="contained"
                color="success"
                size="large"
                sx={{
                  fontWeight: 700,
                  mt: 1,
                  background: "#2284a1",
                  '&:hover': { background: "#0B2132" }
                }}
                disabled={loading}
                fullWidth
              >
                {loading ? "Salvando..." : "Salvar Conexão"}
              </Button>
              <Button
                variant="text"
                color="primary"
                onClick={() => navigate("/dashboard")}
                fullWidth
                type="button"
              >
                Voltar ao Dashboard
              </Button>
              <Button
                variant="text"
                color="secondary"
                onClick={onLogout}
                fullWidth
                type="button"
              >
                Sair
              </Button>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
