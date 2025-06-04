import React from "react";
import { useNavigate } from "react-router-dom";

export default function Navbar({ onLogout, showBack }) {
  const navigate = useNavigate();
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      background: "#222",
      color: "#fff",
      padding: "8px 20px",
      justifyContent: "space-between"
    }}>
      <div>
        <b>IA KPI</b>
        {showBack && <button onClick={() => navigate("/dashboard")} style={{ marginLeft: 10 }}>Voltar</button>}
      </div>
      <button onClick={onLogout} style={{ background: "#F33", color: "#fff", border: "none", padding: "8px 12px", borderRadius: 5 }}>Sair</button>
    </div>
  );
}
