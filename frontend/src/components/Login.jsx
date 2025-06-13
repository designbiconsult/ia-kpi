import React, { useState } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Alert, Stack, Avatar
} from '@mui/material';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    setErro('');
    setLoading(true);

    // Troque pelo seu axios/post
    setTimeout(() => {
      setLoading(false);
      if (email === "admin@teste.com" && senha === "123") {
        onLogin && onLogin({ email });
      } else {
        setErro('E-mail ou senha inválidos!');
      }
    }, 1000);
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
              {/* Pode pôr a logo da empresa aqui */}
              <span role="img" aria-label="Logo">🔑</span>
            </Avatar>
            <Typography variant="h5" fontWeight={700} color="#0B2132">
              Bem-vindo ao IA-KPI
            </Typography>
            <Typography color="text.secondary" fontSize={16}>
              Faça login para acessar o sistema
            </Typography>
          </Stack>

          <form onSubmit={handleLogin} autoComplete="off">
            <Stack spacing={2}>
              <TextField
                label="E-mail"
                variant="outlined"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                fullWidth
                required
              />
              <TextField
                label="Senha"
                variant="outlined"
                type="password"
                value={senha}
                onChange={e => setSenha(e.target.value)}
                fullWidth
                required
              />
              {erro && <Alert severity="error">{erro}</Alert>}
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
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
