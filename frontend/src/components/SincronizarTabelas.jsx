import React, { useEffect, useState } from 'react';
import {
  Box, Card, CardContent, Typography, Button, Checkbox,
  FormControlLabel, Stack, Divider, CircularProgress, Snackbar, Alert
} from '@mui/material';
import axios from 'axios';

export default function SincronizarTabelas({ usuarioId }) {
  const [sincronizadas, setSincronizadas] = useState([]);
  const [novas, setNovas] = useState([]);
  const [selSync, setSelSync] = useState([]);
  const [selNovas, setSelNovas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState({ open: false, text: '', severity: 'success' });

  const fetchTabelas = () => {
    setLoading(true);
    axios.get(`/sincronismo/tabelas?usuario_id=${usuarioId}`).then(res => {
      setSincronizadas(res.data.sincronizadas || []);
      setNovas(res.data.novas || []);
      setSelSync([]); setSelNovas([]);
    }).catch(() => {
      setMsg({ open: true, text: "Erro ao carregar tabelas.", severity: 'error' });
    }).finally(() => setLoading(false));
  };

  useEffect(fetchTabelas, [usuarioId]);

  // Selecionar tudo/desmarcar
  const toggleAllSync = () =>
    setSelSync(selSync.length === sincronizadas.length ? [] : [...sincronizadas]);
  const toggleAllNovas = () =>
    setSelNovas(selNovas.length === novas.length ? [] : [...novas]);

  // Marcar/desmarcar item individual
  const toggleSelSync = tabela =>
    setSelSync(selSync.includes(tabela)
      ? selSync.filter(t => t !== tabela)
      : [...selSync, tabela]);
  const toggleSelNovas = tabela =>
    setSelNovas(selNovas.includes(tabela)
      ? selNovas.filter(t => t !== tabela)
      : [...selNovas, tabela]);

  // Sincronizar/atualizar
  const atualizar = () => {
    if (!selSync.length) return setMsg({ open: true, text: "Selecione ao menos uma tabela sincronizada!", severity: 'warning' });
    setLoading(true);
    axios.post('/sincronismo/atualizar', { usuario_id: usuarioId, tabelas: selSync })
      .then(() => {
        fetchTabelas();
        setMsg({ open: true, text: "Atualizado com sucesso!", severity: 'success' });
      })
      .catch(() => setMsg({ open: true, text: "Erro ao atualizar.", severity: 'error' }))
      .finally(() => setLoading(false));
  };
  const atualizarTodas = () => {
    if (!sincronizadas.length) return setMsg({ open: true, text: "Não há tabelas sincronizadas!", severity: 'warning' });
    setLoading(true);
    axios.post('/sincronismo/atualizar', { usuario_id: usuarioId, tabelas: sincronizadas })
      .then(() => {
        fetchTabelas();
        setMsg({ open: true, text: "Todas atualizadas!", severity: 'success' });
      })
      .catch(() => setMsg({ open: true, text: "Erro ao atualizar.", severity: 'error' }))
      .finally(() => setLoading(false));
  };
  const sincronizarNovas = () => {
    if (!selNovas.length) return setMsg({ open: true, text: "Selecione ao menos uma nova tabela!", severity: 'warning' });
    setLoading(true);
    axios.post('/sincronismo/sincronizar-novas', { usuario_id: usuarioId, tabelas: selNovas })
      .then(() => {
        fetchTabelas();
        setMsg({ open: true, text: "Sincronizado com sucesso!", severity: 'success' });
      })
      .catch(() => setMsg({ open: true, text: "Erro ao sincronizar.", severity: 'error' }))
      .finally(() => setLoading(false));
  };

  return (
    <Box display="flex" gap={4} mt={3} flexWrap="wrap">
      {/* Tabelas Sincronizadas */}
      <Card sx={{ flex: 1, minWidth: 300 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>Tabelas já sincronizadas</Typography>
          <Stack direction="row" spacing={2} mb={2}>
            <Button
              variant="outlined"
              onClick={toggleAllSync}
              size="small"
              disabled={!sincronizadas.length}
            >
              {selSync.length === sincronizadas.length ? "Desmarcar tudo" : "Selecionar tudo"}
            </Button>
            <Button
              variant="contained"
              onClick={atualizar}
              size="small"
              disabled={loading || !selSync.length}
            >
              Atualizar selecionadas
            </Button>
            <Button
              variant="contained"
              color="secondary"
              onClick={atualizarTodas}
              size="small"
              disabled={loading || !sincronizadas.length}
            >
              Atualizar todas
            </Button>
          </Stack>
          <Divider sx={{ mb: 1 }} />
          {loading ? <CircularProgress size={32} /> : (
            <Stack>
              {sincronizadas.length === 0 && <Typography color="text.secondary">Nenhuma tabela sincronizada.</Typography>}
              {sincronizadas.map(t =>
                <FormControlLabel
                  key={t}
                  control={
                    <Checkbox
                      checked={selSync.includes(t)}
                      onChange={() => toggleSelSync(t)}
                    />
                  }
                  label={t}
                />
              )}
            </Stack>
          )}
        </CardContent>
      </Card>

      {/* Novas Tabelas */}
      <Card sx={{ flex: 1, minWidth: 300 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>Novas tabelas disponíveis</Typography>
          <Stack direction="row" spacing={2} mb={2}>
            <Button
              variant="outlined"
              onClick={toggleAllNovas}
              size="small"
              disabled={!novas.length}
            >
              {selNovas.length === novas.length ? "Desmarcar tudo" : "Selecionar tudo"}
            </Button>
            <Button
              variant="contained"
              color="success"
              onClick={sincronizarNovas}
              size="small"
              disabled={loading || !selNovas.length}
            >
              Sincronizar selecionadas
            </Button>
          </Stack>
          <Divider sx={{ mb: 1 }} />
          {loading ? <CircularProgress size={32} /> : (
            <Stack>
              {novas.length === 0 && <Typography color="text.secondary">Nenhuma nova tabela encontrada.</Typography>}
              {novas.map(t =>
                <FormControlLabel
                  key={t}
                  control={
                    <Checkbox
                      checked={selNovas.includes(t)}
                      onChange={() => toggleSelNovas(t)}
                    />
                  }
                  label={t}
                />
              )}
            </Stack>
          )}
        </CardContent>
      </Card>

      {/* Snackbar de mensagem */}
      <Snackbar
        open={msg.open}
        autoHideDuration={3000}
        onClose={() => setMsg(msg => ({ ...msg, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={msg.severity} variant="filled">{msg.text}</Alert>
      </Snackbar>
    </Box>
  );
}
