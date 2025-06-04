import React from 'react';

function SetorTabs({ setores, setor, setSetor }) {
  return (
    <div style={{ marginBottom: 20 }}>
      {setores.map(s =>
        <button
          key={s}
          onClick={() => setSetor(s)}
          style={{
            background: setor === s ? '#02848a' : '#eee',
            color: setor === s ? '#fff' : '#222',
            marginRight: 10,
            padding: "6px 14px",
            border: "none",
            borderRadius: 6,
            cursor: "pointer"
          }}>
          {s}
        </button>
      )}
    </div>
  );
}

export default SetorTabs;
