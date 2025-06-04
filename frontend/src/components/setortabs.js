import React from "react";

export default function SetorTabs({ setores, setor, setSetor }) {
  return (
    <div style={{ margin: "20px 0" }}>
      {setores.map(s => (
        <button
          key={s}
          onClick={() => setSetor(s)}
          style={{
            padding: "8px 16px",
            marginRight: 8,
            background: setor === s ? "#02848a" : "#f0f0f0",
            color: setor === s ? "#fff" : "#333",
            border: "none",
            borderRadius: 6
          }}
        >
          {s}
        </button>
      ))}
    </div>
  );
}
