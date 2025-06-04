import React from 'react';

function IndicadorCard({ indicador }) {
  return (
    <div style={{
      minWidth: 220,
      minHeight: 90,
      border: "1px solid #eee",
      borderRadius: 10,
      boxShadow: "0 1px 4px #0002",
      margin: 10,
      padding: 12,
      background: "#fff"
    }}>
      <div><b>{indicador.nome}</b></div>
      <div>{indicador.valor !== undefined ? indicador.valor : "Sem valor"}</div>
      <div style={{ fontSize: 13, color: "#777" }}>{indicador.descricao}</div>
    </div>
  );
}

export default IndicadorCard;
