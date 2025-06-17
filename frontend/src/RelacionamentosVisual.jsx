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
import { api } from "./api";

// Configurações do canvas e tamanho mínimo dos nodes
const minNodeWidth = 170;
const minNodeHeight = 40;
const canvasWidth = 2600;
const canvasHeight = 1600;

const dragBounds = {
  left: 0,
  top: 0,
  right: canvasWidth - minNodeWidth,
  bottom: canvasHeight - minNodeHeight
};

// Node customizado estilo Power BI
function TableNode({ data, selected }) {
  return (
    <div
      style={{
        background: "#fff",
        border: "2.5px solid #2284a1",
        borderRadius: 16,
        minWidth: minNodeWidth,
        maxWidth: 360,
        boxShadow: "0 2px 16px #2284a128",
        padding: 13,
        position: "relative",
        height: "100%",
        boxSizing: "border-box",
        overflow: "hidden"
      }}
    >
      <NodeResizer
        color="#0B2132"
        isVisible={selected}
        minWidth={minNodeWidth}
        minHeight={minNodeHeight}
        lineStyle={{ borderWidth: 2 }}
      />
      <div style={{ fontWeight: 700, color: "#0B2132", marginBottom: 12, fontSize: 19, letterSpacing: 0.5 }}>
        {data.label}
      </div>
      <div style={{ maxHeight: 340, overflowY: "auto" }}>
        {data.columns.map((col) => (
          <div
            key={col}
            style={{
              margin: "7px 0",
              padding: "6px 14px",
              borderRadius: 8,
              background: "#e4f3fa",
              fontSize: 15.5,
              position: "relative",
              cursor: "crosshair"
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

        // Distribuição grid dinâmica, máximo 6 por linha
        const colCount = Math.min(6, Math.max(1, Math.ceil(Math.sqrt(tabelas.length))));
        const rowCount = Math.ceil(tabelas.length / colCount);
        const spacingX = Math.floor((canvasWidth - 120) / (colCount + 1));
        const spacingY = Math.floor((canvasHeight - 60) / (rowCount + 1));

        const initialNodes = tabelas.map((t, idx) => {
          const row = Math.floor(idx / colCount);
          const col = idx % colCount;
          return {
            id: t,
            type: "table",
            data: { label: t, columns: colunasPorTabela[t] },
            position: {
              x: 80 + col * spacingX,
              y: 40 + row * spacingY,
            },
            style: { minWidth: minNodeWidth, minHeight: minNodeHeight },
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
        height: "93vh",
        background: "#d3e2ed", // Fora do canvas
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
          background: "#f6fbfe",
          border: "7px solid #1976d2",
          borderRadius: 40,
          boxSizing: "border-box",
          position: "relative",
          boxShadow: "0 4px 32px #1976d224",
          overflow: "hidden",
          margin: "38px 0"
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
