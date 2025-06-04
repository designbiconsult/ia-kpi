import React from "react";

export default function IndicadorCard({ titulo, valor }) {
  return (
    <div style={{
      border: "1px solid #eee",
      borderRadius: 10,
      padding: 24,
      width: 220,
      background: "#fafbfc",
      boxShadow: "0 2px 6px #0001"
    }}>
      <div style={{ fontWeight: "bold", fontSize: 18 }}>{titulo}</div>
      <div style={{ fontSize: 28, color: "#02848a", marginTop: 12 }}>{valor}</div>
    </div>
  );
}
