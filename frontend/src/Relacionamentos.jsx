import React, { useEffect, useState } from 'react';
import {
  Box, Card, CardContent, Typography, Button, Stack, TextField, MenuItem, IconButton, Alert, Snackbar
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { api } from './api'; // Sua instância axios

export default function Relacionamentos({ user }) {
  const [relacionamentos, setRelacionamentos] = useState([]);
  const [tabelas, setTabelas] = useState([]);
  const [colunasOrigem, setColunasOrigem] = useState([]);
  const [colunasDestino, setColunasDestino] = useState([]);
  const [form, setForm] = useState({
    tabela_origem: '',
    coluna_origem: '',
    tabela_destino: '',
    coluna_destino: '',
    tipo_relacionamento: ''
  });
  const [msg, setMsg] = useState({ open: false, text: '', severity: 'success' });

  // Carregar relacionamentos
  const fetchRelacionamentos = () => {
    api.get('/relacionamentos', {
      params: { empresa_id: user.empresa_id, email: user.email, senha: user.senha }
    }).then(res => setRelacionamentos(res.data || []));
  };

  // Carregar tabelas sincronizadas
  const fetchTabelas = () => {
    api.get('/tabelas/listar', {
      params: { empresa_id: user.empresa_id }
    }).then(res => setTabelas(res.data || []));
  };

  useEffect(() => {
  // Só faz as chamadas se user está definido E empresa_id existe
  if (user && user.empresa_id) {
    fetchRelacionamentos();
    fetchTabelas();
  }
}, [user]);


  // Carregar colunas ao escolher tabela
  useEffect(() => {
    if (form.tabela_origem)
      api.get('/tabelas/colunas', { params: { tabela: form.tabela_origem } })
        .then(res => setColunasOrigem(res.data || []));
    else
      setColunasOrigem([]);
    setForm(f => ({ ...f, coluna_origem: '' }));
  }, [form.tabela_origem]);
  useEffect(() => {
    if (form.tabela_destino)
      api.get('/tabelas/colunas', { params: { tabela: form.tabela_destino } })
        .then(res => setColunasDestino(res.data || []));
    else
      setColunasDestino([]);
    setForm(f => ({ ...f, coluna_destino: '' }));
  }, [form.tabela_destino]);

  // Submeter relacionamento
  const handleSubmit = async e => {
    e.preventDefault();
    if (!form.tabela_origem || !form.coluna_origem || !form.tabela_destino || !form.coluna_destino || !form.tipo_relacionamento)
      return setMsg({ open: true, text: 'Preencha todos os campos.', severity: 'warning' });
    try {
      await api.post('/relacionamentos', {
        ...form,
        empresa_id: user.empresa_id,
        email: user.email,
        senha: user.senha
      });
      setMsg({ open: true, text: 'Relacionamento salvo!', severity: 'success' });
      setForm({ tabela_origem: '', coluna_origem: '', tabela_destino: '', coluna_destino: '', tipo_relacionamento: '' });
      fetchRelacionamentos();
    } catch (err) {
      setMsg({ open: true, text: 'Erro ao salvar relacionamento.', severity: 'error' });
    }
  };

  // Excluir
  const handleDelete = async id => {
    if (!window.confirm("Remover esse relacionamento?")) return;
    try {
      await api.delete(`/relacionamentos/${id}`, {
        params: { email: user.email, senha: user.senha }
      });
      setMsg({ open: true, text: 'Removido!', severity: 'success' });
      fetchRelacionamentos();
    } catch (err) {
      setMsg({ open: true, text: 'Erro ao remover.', severity: 'error' });
    }
  };

  return (
    <Box minHeight="100vh" sx={{ background: 'linear-gradient(120deg, #f8fafd 60%, #e4f3fa 100%)', py: 6 }}>
      <Card sx={{ maxWidth: 700, mx: 'auto', borderRadius: 4, boxShadow: '0 4px 32px #6fc7ea18' }}>
        <CardContent>
          <Typography variant="h5" fontWeight={700} color="#0B2132" mb={2}>Relacionamentos entre tabelas</Typography>
          <form onSubmit={handleSubmit}>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2} mb={2}>
              <TextField
                select label="Tabela Origem" value={form.tabela_origem}
                onChange={e => setForm(f => ({ ...f, tabela_origem: e.target.value }))}
                sx={{ minWidth: 140 }} required>
                <MenuItem value="">Selecione...</MenuItem>
                {tabelas.map(t => <MenuItem key={t} value={t}>{t}</MenuItem>)}
              </TextField>
              <TextField
                select label="Coluna Origem" value={form.coluna_origem}
                onChange={e => setForm(f => ({ ...f, coluna_origem: e.target.value }))}
                sx={{ minWidth: 120 }} required>
                <MenuItem value="">Selecione...</MenuItem>
                {colunasOrigem.map(c => <MenuItem key={c} value={c}>{c}</MenuItem>)}
              </TextField>
              <TextField
                select label="Tabela Destino" value={form.tabela_destino}
                onChange={e => setForm(f => ({ ...f, tabela_destino: e.target.value }))}
                sx={{ minWidth: 140 }} required>
                <MenuItem value="">Selecione...</MenuItem>
                {tabelas.map(t => <MenuItem key={t} value={t}>{t}</MenuItem>)}
              </TextField>
              <TextField
                select label="Coluna Destino" value={form.coluna_destino}
                onChange={e => setForm(f => ({ ...f, coluna_destino: e.target.value }))}
                sx={{ minWidth: 120 }} required>
                <MenuItem value="">Selecione...</MenuItem>
                {colunasDestino.map(c => <MenuItem key={c} value={c}>{c}</MenuItem>)}
              </TextField>
              <TextField
                select label="Tipo" value={form.tipo_relacionamento}
                onChange={e => setForm(f => ({ ...f, tipo_relacionamento: e.target.value }))}
                sx={{ minWidth: 100 }} required>
                <MenuItem value="">Tipo</MenuItem>
                <MenuItem value="1-1">1-1</MenuItem>
                <MenuItem value="1-N">1-N</MenuItem>
                <MenuItem value="N-N">N-N</MenuItem>
              </TextField>
              <Button type="submit" variant="contained" color="primary" sx={{ minWidth: 130, fontWeight: 700 }}>
                Salvar
              </Button>
            </Stack>
          </form>
          {relacionamentos.length === 0 ? (
            <Typography color="text.secondary" mt={2}>Nenhum relacionamento cadastrado.</Typography>
          ) : (
            <Stack spacing={1} mt={2}>
              {relacionamentos.map(rel => (
                <Box
                  key={rel.id}
                  sx={{
                    p: 1.2,
                    borderRadius: 2,
                    bgcolor: "#f2f6fc",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between"
                  }}>
                  <span>
                    <b>{rel.tabela_origem}.{rel.coluna_origem}</b> → <b>{rel.tabela_destino}.{rel.coluna_destino}</b> ({rel.tipo_relacionamento})
                  </span>
                  <IconButton size="small" color="error" onClick={() => handleDelete(rel.id)}>
                    <DeleteIcon />
                  </IconButton>
                </Box>
              ))}
            </Stack>
          )}
        </CardContent>
      </Card>
      <Snackbar open={msg.open} autoHideDuration={3200} onClose={() => setMsg(m => ({ ...m, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert severity={msg.severity} variant="filled">{msg.text}</Alert>
      </Snackbar>
    </Box>
  );
}
