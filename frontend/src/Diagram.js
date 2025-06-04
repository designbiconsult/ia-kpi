import React from "react";
import ReactFlow, { MiniMap, Controls, Background } from "react-flow-renderer";
import axios from "axios";

export default function Diagram({ tabelas, colunas, relacionamentos, setRelacionamentos }) {
  const nodes = tabelas.map((tb, idx) => ({
    id: tb,
    data: { label: tb },
    position: { x: 200 * idx, y: 100 },
    style: { minWidth: 150, minHeight: 60, background: "#f0f4f8", border: "1px solid #02848a", borderRadius: 12, padding: 6 }
  }));

  const edges = relacionamentos.map(rel => ({
    id: "edge_" + rel.id,
    source: rel.tabela_origem,
    sourceHandle: rel.coluna_origem,
    target: rel.tabela_destino,
    targetHandle: rel.coluna_destino,
    label: rel.tipo_relacionamento,
    animated: true,
    style: { stroke: "#02848a" }
  }));

  const onConnect = (params) => {
    const rel = {
      tabela_origem: params.source,
      coluna_origem: params.sourceHandle,
      tabela_destino: params.target,
      coluna_destino: params.targetHandle,
      tipo_relacionamento: window.prompt("Tipo de relacionamento (1:1, 1:N, N:1, N:N)", "1:N") || "N:N"
    };
    axios.post("http://localhost:8000/relacionamentos", rel).then(() => {
      axios.get("http://localhost:8000/relacionamentos").then(res => setRelacionamentos(res.data));
    });
  };

  const nodeTypes = {
    default: ({ data, id }) => (
      <div>
        <div style={{ fontWeight: "bold", color: "#02848a", marginBottom: 8 }}>{data.label}</div>
        {(colunas[id] || []).map(col => (
          <div key={col} style={{ fontSize: 13, color: "#222" }}>
            <span data-handle-id={col}>{col}</span>
          </div>
        ))}
      </div>
    )
  };

  return (
    <ReactFlow
      elements={[...nodes, ...edges]}
      nodeTypes={nodeTypes}
      onConnect={onConnect}
      snapToGrid={true}
      style={{ width: "100vw", height: "90vh" }}
    >
      <MiniMap />
      <Controls />
      <Background />
    </ReactFlow>
  );
}
