import React, { useState } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Alert, Stack
} from '@mui/material';
import axios from 'axios';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    setErro('');
    setLoading(true);

    axios.post('/login', { email, senha })
      .then(res => {
        onLogin && onLogin(res.data);
      })
      .catch(() => setErro('E-mail ou senha inválidos!'))
      .finally(() => setLoading(false));
  };

  return (
    <Box
      minHeight="100vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
      sx={{ background: "#f8fafd" }}
    >
      <Card sx={{
        minWidth: 350,
        maxWidth: 400,
        px: 3, py: 4,
        borderRadius: 4,
        boxShadow: 3,
        background: "#fff"
      }}>
        <CardContent>
          <Typography variant="h5" fontWeight={700} textAlign="center" mb={2}>
            IA-KPI - Login
          </Typography>

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
                sx={{ fontWeight: 700, mt: 1 }}
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
