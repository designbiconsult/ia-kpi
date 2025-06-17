import React, { useEffect, useState, useCallback } from "react";
import ReactFlow, {
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  NodeResizer,
  Handle,
  Position
} from "reactflow";
import "reactflow/dist/style.css";
import { api } from "./api";

// ... (TableNode igual ao anterior)

const minNodeWidth = 170;
const minNodeHeight = 40;
const canvasWidth = 2600;
const canvasHeight = 1600;

// REMOVE nodeDragBounds!
// const dragBounds = { ... }

function RelacionamentosBI({ user }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

  // **BLOQUEIA O NODE NA BORDA CORRETAMENTE!**
  const onNodesChangeFixed = useCallback(
    (changes) => {
      const fixedChanges = changes.map((change) => {
        if (change.type === "position" && change.position) {
          let { x, y } = change.position;
          // Não deixa passar das bordas!
          x = Math.max(0, Math.min(x, canvasWidth - minNodeWidth));
          y = Math.max(0, Math.min(y, canvasHeight - minNodeHeight));
          return { ...change, position: { x, y } };
        }
        return change;
      });
      onNodesChange(fixedChanges);
    },
    [onNodesChange]
  );

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
        background: "#d3e2ed",
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
          onNodesChange={onNodesChangeFixed}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
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
