import React, { useEffect, useState } from "react";
import ReactFlow, {
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  NodeResizer,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { api } from "./api"; // Seu axios customizado

function TableNode({ data, selected }) {
  return (
    <div
      style={{
        background: "#fff",
        border: "2.5px solid #2284a1",
        borderRadius: 12,
        minWidth: 120,
        maxWidth: 380,
        boxShadow: "0 2px 16px #2284a128",
        padding: 10,
        position: "relative",
        height: "100%",
        boxSizing: "border-box",
        overflow: "hidden"
      }}
    >
      <NodeResizer
        color="#0B2132"
        isVisible={selected}
        minWidth={90}
        minHeight={34}
        lineStyle={{ borderWidth: 2 }}
      />
      <div style={{ fontWeight: 700, color: "#0B2132", marginBottom: 8, fontSize: 18 }}>
        {data.label}
      </div>
      <div style={{ maxHeight: 320, overflowY: "auto" }}>
        {data.columns.map((col) => (
          <div
            key={col}
            style={{
              margin: "5px 0",
              padding: "5px 8px",
              borderRadius: 6,
              background: "#e4f3fa",
              fontSize: 14,
              position: "relative",
              cursor: "crosshair",
            }}
          >
            <Handle
              type="source"
              id={`${data.label}.${col}`}
              position={Position.Right}
              style={{
                background: "rgba(0,0,0,0)",
                width: 12,
                height: 12,
                top: "50%",
                right: -6,
                transform: "translateY(-50%)",
              }}
            />
            <Handle
              type="target"
              id={`${data.label}.${col}`}
              position={Position.Left}
              style={{
                background: "rgba(0,0,0,0)",
                width: 12,
                height: 12,
                top: "50%",
                left: -6,
                transform: "translateY(-50%)",
              }}
            />
            {col}
          </div>
        ))}
      </div>
    </div>
  );
}
const nodeTypes = { table: TableNode };

function RelacionamentosBI({ user }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

  // Tamanho do canvas
  const canvasWidth = 1600;
  const canvasHeight = 900;
  const dragBounds = { left: 0, top: 0, right: canvasWidth, bottom: canvasHeight };

  // Carregar tabelas + colunas do backend
  useEffect(() => {
    if (!user?.empresa_id) return;
    setLoading(true);
    api.get("/tabelas/listar", { params: { empresa_id: user.empresa_id } })
      .then(async (tabRes) => {
        const tabelas = tabRes.data || [];
        const colunasPorTabela = {};
        await Promise.all(
          tabelas.map(async (t) => {
            const resp = await api.get("/tabelas/colunas", { params: { tabela: t } });
            colunasPorTabela[t] = resp.data || [];
          })
        );

        // Distribuir as tabelas automaticamente (em linhas e colunas)
        const colCount = Math.max(1, Math.ceil(Math.sqrt(tabelas.length)));
        const rowCount = Math.ceil(tabelas.length / colCount);
        const spacingX = Math.floor((canvasWidth - 120) / Math.max(1, colCount));
        const spacingY = Math.floor((canvasHeight - 60) / Math.max(1, rowCount));

        const initialNodes = tabelas.map((t, idx) => {
          const row = Math.floor(idx / colCount);
          const col = idx % colCount;
          return {
            id: t,
            type: "table",
            data: { label: t, columns: colunasPorTabela[t] },
            position: {
              x: 40 + col * spacingX,
              y: 30 + row * spacingY,
            },
            style: { minWidth: 140, minHeight: 60 },
            resizable: true,
          };
        });

        setNodes(initialNodes);
        setLoading(false);
      });
  }, [user]);

  return (
    <div
      style={{
        width: "100vw",
        height: "90vh",
        background: "#cfd8dc", // Fora do canvas (cinza claro)
        overflow: "auto",
        position: "relative",
        display: "flex",
        justifyContent: "center",
        alignItems: "center"
      }}
    >
      <div
        style={{
          width: canvasWidth,
          height: canvasHeight,
          background: "#e4f3fa",
          border: "6px solid #06597a", // **Borda GROSSA, visível**
          borderRadius: 32,
          boxSizing: "border-box",
          position: "relative",
          boxShadow: "0 4px 42px #0b213214",
          overflow: "hidden",
          margin: "32px 0"
        }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          nodeDragBounds={dragBounds}
          panOnDrag={false}
          nodesDraggable
          nodesConnectable
          fitView={false}
        />
      </div>
    </div>
  );
}

export default function RelacionamentosVisual({ user }) {
  return (
    <ReactFlowProvider>
      <RelacionamentosBI user={user} />
    </ReactFlowProvider>
  );
}
