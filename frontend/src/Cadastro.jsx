import React, { useState } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Alert, Stack, Avatar
} from '@mui/material';
import { useNavigate } from "react-router-dom";
import { api } from './api';

export default function Cadastro() {
  const [form, setForm] = useState({
    nome: '',
    email: '',
    senha: '',
    senha2: '',
  });
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = e =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleCadastro = async e => {
    e.preventDefault();
    setErro('');
    setSucesso('');

    if (!form.nome || !form.email || !form.senha || !form.senha2) {
      setErro("Preencha todos os campos!");
      return;
    }
    if (form.senha !== form.senha2) {
      setErro("As senhas não coincidem!");
      return;
    }

    setLoading(true);
    try {
      await api.post("/usuarios", {
        nome: form.nome,
        email: form.email,
        senha: form.senha
      });
      setSucesso("Cadastro realizado com sucesso! Faça login.");
      setTimeout(() => navigate("/"), 1200); // Vai para login após 1,2s
    } catch (err) {
      if (err.response?.data?.detail === "Email já cadastrado")
        setErro("Email já cadastrado!");
      else
        setErro("Ocorreu um erro ao cadastrar. Tente novamente.");
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
        maxWidth: 420,
        px: 4, py: 5,
        borderRadius: 4,
        boxShadow: '0 4px 32px #6fc7ea18'
      }}>
        <CardContent>
          <Stack spacing={2} alignItems="center" mb={2}>
            <Avatar sx={{ width: 56, height: 56, bgcolor: '#2284a1', fontSize: 32 }}>
              <span role="img" aria-label="Cadastro">📝</span>
            </Avatar>
            <Typography variant="h5" fontWeight={700} color="#2284a1">
              Criar Conta
            </Typography>
            <Typography color="text.secondary" fontSize={16}>
              Preencha os dados para cadastrar-se
            </Typography>
          </Stack>
          <form onSubmit={handleCadastro} autoComplete="off">
            <Stack spacing={2}>
              <TextField
                label="Nome"
                name="nome"
                variant="outlined"
                value={form.nome}
                onChange={handleChange}
                fullWidth
                required
                autoFocus
              />
              <TextField
                label="E-mail"
                name="email"
                type="email"
                variant="outlined"
                value={form.email}
                onChange={handleChange}
                fullWidth
                required
              />
              <TextField
                label="Senha"
                name="senha"
                type="password"
                variant="outlined"
                value={form.senha}
                onChange={handleChange}
                fullWidth
                required
              />
              <TextField
                label="Repita a senha"
                name="senha2"
                type="password"
                variant="outlined"
                value={form.senha2}
                onChange={handleChange}
                fullWidth
                required
              />
              {erro && <Alert severity="error">{erro}</Alert>}
              {sucesso && <Alert severity="success">{sucesso}</Alert>}
              <Button
                variant="contained"
                color="success"
                type="submit"
                disabled={loading}
                size="large"
                sx={{
                  fontWeight: 700,
                  mt: 1,
                  background: "#2284a1",
                  '&:hover': { background: "#0B2132" }
                }}
                fullWidth
              >
                {loading ? 'Cadastrando...' : 'Cadastrar'}
              </Button>
              <Button
                variant="text"
                color="primary"
                onClick={() => navigate("/")}
                fullWidth
                sx={{ mt: 0.5 }}
                type="button"
              >
                Já tem conta? Entrar
              </Button>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
