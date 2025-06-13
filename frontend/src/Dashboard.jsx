import React from "react";
import {
  Box, Typography, Stack, Card, CardContent, Avatar, Grid, Button
} from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function Dashboard({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout && onLogout();    // Limpa user no App.jsx e localStorage
    navigate("/login");        // Volta para login
  };

  // Exemplos de indicadores (pode vir da API futuramente)
  const indicadores = [
    {
      titulo: "Receitas do mês",
      valor: "R$ 100.000",
      icon: "💰",
      cor: "#0B2132"
    },
    {
      titulo: "Despesas do mês",
      valor: "R$ 45.500",
      icon: "📉",
      cor: "#d32f2f"
    },
    {
      titulo: "Saldo em Caixa",
      valor: "R$ 54.500",
      icon: "💵",
      cor: "#2284a1"
    }
  ];

  return (
    <Box sx={{
      minHeight: "100vh",
      background: "linear-gradient(120deg, #f8fafd 60%, #e4f3fa 100%)",
      py: 5, px: 2
    }}>
      {/* Navbar fictícia */}
      <Stack direction="row" justifyContent="flex-end" alignItems="center" spacing={2} mb={4}>
        <Avatar sx={{ bgcolor: "#2284a1" }}>{user?.nome?.[0]?.toUpperCase() || "U"}</Avatar>
        <Typography fontWeight={600}>{user?.nome || "Usuário"}</Typography>
        <Button
          variant="outlined"
          color="secondary"
          onClick={handleLogout}
        >Sair</Button>
      </Stack>

      {/* Título de boas-vindas */}
      <Typography variant="h4" fontWeight={700} color="#0B2132" mb={2}>
        Bem-vindo, {user?.nome?.split(" ")[0] || "usuário"}!
      </Typography>
      <Typography color="text.secondary" mb={4}>
        Aqui estão seus principais indicadores do mês:
      </Typography>

      {/* Cards de indicadores */}
      <Grid container spacing={3} justifyContent="center">
        {indicadores.map((ind, idx) => (
          <Grid item xs={12} sm={6} md={4} key={ind.titulo}>
            <Card sx={{ borderRadius: 4, boxShadow: 2 }}>
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center">
                  <Avatar sx={{
                    bgcolor: ind.cor,
                    width: 48,
                    height: 48,
                    fontSize: 28
                  }}>{ind.icon}</Avatar>
                  <Box>
                    <Typography color="text.secondary" fontSize={16}>{ind.titulo}</Typography>
                    <Typography fontWeight={700} fontSize={22} color={ind.cor}>{ind.valor}</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Botões rápidos (exemplo) */}
      <Stack direction="row" spacing={2} mt={5} justifyContent="center">
        <Button
          variant="contained"
          color="primary"
          size="large"
          sx={{ fontWeight: 700, background: "#0B2132", '&:hover': { background: "#06597a" } }}
          onClick={() => navigate("/sincronismo")}
        >
          Sincronizar Tabelas
        </Button>
        <Button
          variant="contained"
          color="success"
          size="large"
          sx={{ fontWeight: 700, background: "#2284a1", '&:hover': { background: "#0B2132" } }}
          onClick={() => navigate("/conexao")}
        >
          Configurar Conexão
        </Button>
      </Stack>
    </Box>
  );
}
