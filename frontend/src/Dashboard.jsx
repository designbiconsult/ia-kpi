import React from "react";
import {
  Box, Typography, Stack, Card, CardContent, Avatar, Grid
} from "@mui/material";

export default function Dashboard({ user }) {
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
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "90vh",
        background: "linear-gradient(120deg, #f8fafd 60%, #e4f3fa 100%)",
        py: 4,
        px: 2
      }}
    >
      <Box
        sx={{
          width: "100%",
          maxWidth: 820,
          bgcolor: "#fff",
          borderRadius: 4,
          boxShadow: "0 2px 24px #0B213220",
          p: { xs: 2, md: 5 },
          mx: "auto"
        }}
      >
        <Typography variant="h4" fontWeight={700} color="#0B2132" mb={2}>
          Bem-vindo, {user?.nome?.split(" ")[0] || "usuário"}!
        </Typography>
        <Typography color="text.secondary" mb={4}>
          Aqui estão seus principais indicadores do mês:
        </Typography>

        {/* Cards de indicadores */}
        <Grid container spacing={3} justifyContent="center" mb={1}>
          {indicadores.map((ind, idx) => (
            <Grid item xs={12} sm={6} md={4} key={ind.titulo}>
              <Card sx={{
                borderRadius: 4,
                boxShadow: "0 2px 16px #2284a128",
                transition: 'box-shadow 0.2s',
                '&:hover': { boxShadow: "0 4px 32px #2284a130" }
              }}>
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
      </Box>
    </Box>
  );
}
