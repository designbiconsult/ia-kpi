import React, { useEffect, useState } from "react";
import axios from "axios";
import { Box, Card, CardContent, Typography, Stack } from "@mui/material";

export default function AdminDashboard({ user }) {
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    async function fetchData() {
      try {
        // Use email/senha do user para autenticar
        const { data } = await axios.get("http://localhost:8000/admin/dashboard", {
          data: { email: user.email, senha: user.senha }
        });
        setDados(data);
      } catch (err) {
        setErro("Erro ao buscar dashboard admin.");
      }
    }
    fetchData();
  }, [user]);

  if (erro) return <div>{erro}</div>;
  if (!dados) return <div>Carregando...</div>;

  return (
    <Box>
      <Typography variant="h4" mb={2}>Administração Geral</Typography>
      <Stack direction="row" spacing={2}>
        <Card><CardContent>
          <Typography variant="h6">Empresas</Typography>
          <Typography>{dados.empresas}</Typography>
        </CardContent></Card>
        <Card><CardContent>
          <Typography variant="h6">Usuários</Typography>
          <Typography>{dados.usuarios}</Typography>
        </CardContent></Card>
        <Card><CardContent>
          <Typography variant="h6">Usuários Ativos</Typography>
          <Typography>{dados.usuarios_ativos}</Typography>
        </CardContent></Card>
      </Stack>
    </Box>
  );
}
