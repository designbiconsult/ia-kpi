import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Box, Card, CardContent, Typography, TextField, Button, Alert, Stack } from "@mui/material";

export default function CadastroEmpresa() {
  const [form, setForm] = useState({
    nome_empresa: "",
    nome_usuario: "",
    email: "",
    senha: ""
  });
  const [msg, setMsg] = useState("");
  const [ok, setOk] = useState(false);
  const navigate = useNavigate();

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    setMsg("");
    setOk(false);
    try {
      await axios.post("http://localhost:8000/empresas/cadastro_completo", form);
      setOk(true);
      setTimeout(() => navigate("/login"), 2000);
    } catch (err) {
      setMsg(err.response?.data?.detail || "Erro ao cadastrar.");
    }
  };

  return (
    <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center" sx={{ background: 'linear-gradient(120deg, #f8fafd 60%, #e4f3fa 100%)' }}>
      <Card sx={{ minWidth: 350, maxWidth: 480, px: 3, py: 4, borderRadius: 4, boxShadow: '0 4px 32px #6fc7ea18' }}>
        <CardContent>
          <Stack spacing={2} alignItems="center" mb={2}>
            <Typography variant="h5" fontWeight={700} color="#0B2132">
              Cadastro de Empresa
            </Typography>
            <Typography color="text.secondary" fontSize={16}>
              Informe os dados da empresa e do responsável
            </Typography>
          </Stack>
          <form onSubmit={handleSubmit} autoComplete="off">
            <Stack spacing={2}>
              <TextField label="Nome da Empresa" name="nome_empresa" value={form.nome_empresa} onChange={handleChange} required />
              <TextField label="Nome do Usuário Admin" name="nome_usuario" value={form.nome_usuario} onChange={handleChange} required />
              <TextField label="E-mail do Usuário" type="email" name="email" value={form.email} onChange={handleChange} required />
              <TextField label="Senha do Usuário" type="password" name="senha" value={form.senha} onChange={handleChange} required />
              {msg && <Alert severity="error">{msg}</Alert>}
              {ok && <Alert severity="success">Cadastro realizado! Redirecionando para login...</Alert>}
              <Button variant="contained" color="primary" type="submit" sx={{ fontWeight: 700, background: "#0B2132", '&:hover': { background: "#06597a" } }} fullWidth>
                Cadastrar
              </Button>
              <Button onClick={() => navigate("/login")}>Já tenho cadastro</Button>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
