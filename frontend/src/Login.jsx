import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  Box, Card, CardContent, Typography, TextField, Button, Alert, Stack, Avatar
} from "@mui/material";

export default function Login({ onLogin }) {
  const [form, setForm] = useState({ email: "", senha: "" });
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    setMsg("");
    setLoading(true);
    try {
      // ENVIE O LOGIN NO BODY COMO JSON!
      const { data } = await axios.post("http://localhost:8000/login", {
        email: form.email,
        senha: form.senha
      });
      onLogin(data);
      navigate("/dashboard");
    } catch (err) {
      setMsg("Credenciais inválidas.");
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
        minWidth: 340,
        maxWidth: 400,
        px: 4, py: 5,
        borderRadius: 4,
        boxShadow: '0 4px 32px #6fc7ea18'
      }}>
        <CardContent>
          <Stack spacing={2} alignItems="center" mb={2}>
            <Avatar sx={{ width: 56, height: 56, bgcolor: '#0B2132', fontSize: 32 }}>
              <span role="img" aria-label="Logo">🔑</span>
            </Avatar>
            <Typography variant="h5" fontWeight={700} color="#0B2132">
              IA-KPI Login
            </Typography>
            <Typography color="text.secondary" fontSize={16}>
              Acesse sua conta
            </Typography>
          </Stack>
          <form onSubmit={handleSubmit} autoComplete="off">
            <Stack spacing={2}>
              <TextField
                label="E-mail"
                name="email"
                variant="outlined"
                type="email"
                value={form.email}
                onChange={handleChange}
                fullWidth
                required
              />
              <TextField
                label="Senha"
                name="senha"
                variant="outlined"
                type="password"
                value={form.senha}
                onChange={handleChange}
                fullWidth
                required
              />
              {msg && <Alert severity="error">{msg}</Alert>}
              <Button
                variant="contained"
                color="primary"
                type="submit"
                disabled={loading}
                size="large"
                sx={{
                  fontWeight: 700,
                  mt: 1,
                  background: "#0B2132",
                  '&:hover': { background: "#06597a" }
                }}
                fullWidth
              >
                {loading ? 'Entrando...' : 'Entrar'}
              </Button>
              <Button
                color="secondary"
                onClick={() => navigate("/cadastro_empresa")}
                fullWidth
              >
                Cadastrar Empresa
              </Button>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
