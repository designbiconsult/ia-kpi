import React, { useEffect, useState } from 'react';
import { api } from '../api';

const indicadoresPorSetor = {
  "Financeiro": [
    "Receitas do mês",
    "Despesas do mês",
    "Saldo em Caixa"
  ],
  "Comercial": [
    "Total de Vendas",
    "Clientes novos",
    "Ticket médio"
  ],
  "Produção": [
    "Modelos produzidos",
    "Total produzido",
    "Mais produzido"
  ]
};

export default function IndicadoresSetor({ setor }) {
  const [dados, setDados] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.get(`/indicadores?setor=${encodeURIComponent(setor)}`)
      .then(res => setDados(res.data))
      .finally(() => setLoading(false));
  }, [setor]);

  return (
    <div className="indicadores-box">
      {indicadoresPorSetor[setor].map(indicador =>
        <div key={indicador} className="indicador-card">
          <div className="indicador-titulo">{indicador}</div>
          <div className="indicador-valor">
            {loading ? "Carregando..." : (dados[indicador] ?? "--")}
          </div>
        </div>
      )}
    </div>
  );
}
