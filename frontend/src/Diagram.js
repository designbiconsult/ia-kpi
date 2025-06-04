import React, { useEffect, useState } from "react";
import axios from "axios";
import ReactFlow, { MiniMap, Controls, Background } from "reactflow";
import "reactflow/dist/style.css";

function Diagram() {
  const [tables, setTables] = useState([]);
  const [columns, setColumns] = useState({});
  const [edges, setEdges] = useState([]);
  const [nodes, setNodes] = useState([]);

  // Carregar tabelas e colunas
  useEffect(() => {
    axios.get("http://localhost:8000/tabelas").then(r => {
      setTables(r.data);
      r.data.forEach(tab => {
        axios.get(`http://localhost:8000/colunas/${tab}`).then(res => {
          setColumns(cols => ({ ...cols, [tab]: res.data }));
        });
      });
    });
    axios.get("http://localhost:8000/relacionamentos").then(r => {
      setEdges(r.data.map((rel, idx) => ({
        id: "" + rel.id,
        source: rel.tabela_origem,
        target: rel.tabela_destino,
        label: `${rel.coluna_origem} → ${rel.coluna_destino} (${rel.tipo_relacionamento})`,
        animated: true,
        style: { stroke: "#09c" },
      })));
    });
  }, []);

  // Criar nós das tabelas
  useEffect(() => {
    setNodes(
      tables.map((t, idx) => ({
        id: t,
        position: { x: 100 + 250 * (idx % 3), y: 50 + 220 * Math.floor(idx / 3) },
        data: { label: t + "\n" + (columns[t] || []).join(", ") },
        style: { border: "1px solid #aaa", background: "#fff" }
      }))
    );
  }, [tables, columns]);

  return (
    <div style={{ width: "100vw", height: "80vh", background: "#f6fafd" }}>
      <h2 style={{ textAlign: "center" }}>Relacionamentos de Tabelas (Clique e arraste colunas)</h2>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}

export default Diagram;
