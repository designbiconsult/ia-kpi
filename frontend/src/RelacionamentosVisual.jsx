import React, { useEffect, useState, useRef } from "react";
import ReactFlow, {
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { api } from "./api";

// Parâmetros
const minNodeWidth = 160;
const maxNodeWidth = 480;
const minNodeHeight = 48;
const canvasWidth = 2200;
const canvasHeight = 1200;

// Componente do node custom com resize só à direita, nunca expande à esquerda
function TableNode({ id, data, selected, width = minNodeWidth, setNodes }) {
  const nodeRef = useRef(null);
  const [isResizing, setIsResizing] = useState(false);
  const prevWidth = useRef(width);

  useEffect(() => {
    prevWidth.current = width;
  }, [width]);

  useEffect(() => {
    function onMouseMove(e) {
      if (!isResizing || !nodeRef.current) return;

      const rect = nodeRef.current.getBoundingClientRect();
      let nextWidth = Math.max(minNodeWidth, Math.min(maxNodeWidth, e.clientX - rect.left));

      // Só permite crescer para a direita:
      // - Se mouse está indo para a direita (aumentando)
      // - OU se está diminuindo (sempre permite)
      if (nextWidth > prevWidth.current) {
        // Pode aumentar (só indo para a direita)
        setNodes((nds) =>
          nds.map((n) =>
            n.id === id
              ? { ...n, width: nextWidth }
              : n
          )
        );
        prevWidth.current = nextWidth;
      } else if (nextWidth < prevWidth.current) {
        // Pode diminuir à vontade (nunca cresce pra esquerda)
        setNodes((nds) =>
          nds.map((n) =>
            n.id === id
              ? { ...n, width: nextWidth }
              : n
          )
        );
        prevWidth.current = nextWidth;
      }
      // Se mouse está indo pra esquerda e tentaria crescer, ignora!
    }
    function onMouseUp() {
      setIsResizing(false);
    }
    if (isResizing) {
      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
    // eslint-disable-next-line
  }, [isResizing, id, setNodes]);

  return (
    <div
      ref={nodeRef}
      style={{
        background: "#fff",
        border: selected ? "3px solid #0B2132" : "2.5px solid #2284a1",
        borderRadius: 16,
        minWidth: minNodeWidth,
        width: width,
        maxWidth: maxNodeWidth,
        minHeight: minNodeHeight,
        boxShadow: "0 2px 16px #2284a128",
        padding: 13,
        position: "relative",
        transition: "box-shadow 0.15s",
        userSelect: "none",
        overflow: "hidden",
        boxSizing: "border-box"
      }}
    >
      <div style={{
        fontWeight: 700,
        color: "#0B2132",
        marginBottom: 10,
        fontSize: 18,
        letterSpacing: 0.4,
        overflow: "hidden",
        textOverflow: "ellipsis"
      }}>
        {data.label}
      </div>
      <div style={{ maxHeight: 330, overflowY: "auto" }}>
        {data.columns.map((col) => (
          <div
            key={col}
            style={{
              margin: "6px 0",
              padding: "6px 14px",
              borderRadius: 8,
              background: "#e4f3fa",
              fontSize: 15.2,
              position: "relative",
              cursor: "crosshair",
              overflow: "hidden",
              textOverflow: "ellipsis"
            }}
          >
            <Handle
              type="source"
              id={`${data.label}.${col}`}
              position={Position.Right}
              style={{
                background: "rgba(0,0,0,0)",
                width: 13,
                height: 13,
                top: "50%",
                right: -7,
                transform: "translateY(-50%)"
              }}
            />
            <Handle
              type="target"
              id={`${data.label}.${col}`}
              position={Position.Left}
              style={{
                background: "rgba(0,0,0,0)",
                width: 13,
                height: 13,
                top: "50%",
                left: -7,
                transform: "translateY(-50%)"
              }}
            />
            {col}
          </div>
        ))}
      </div>
      {/* Handle para resize só à direita */}
      <div
        onMouseDown={() => setIsResizing(true)}
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          height: "100%",
          width: 9,
          cursor: "ew-resize",
          background: selected ? "#2284a11a" : "transparent",
          zIndex: 2
        }}
        title="Ajustar largura (só à direita)"
      />
    </div>
  );
}

// Wrapper para o node customizado
const NodeWrapper = (setNodes) => (props) => (
  <TableNode {...props} setNodes={setNodes} />
);

function RelacionamentosBI({ user }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

  // Carrega tabelas reais e monta nodes
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

        // Distribuição grid automática
        const colCount = Math.min(6, Math.max(1, Math.ceil(Math.sqrt(tabelas.length))));
        const rowCount = Math.ceil(tabelas.length / colCount);
        const spacingX = Math.floor((canvasWidth - 180) / (colCount + 1));
        const spacingY = Math.floor((canvasHeight - 60) / (rowCount + 1));

        const initialNodes = tabelas.map((t, idx) => {
          const row = Math.floor(idx / colCount);
          const col = idx % colCount;
          return {
            id: t,
            type: "tableNodeCustom",
            data: { label: t, columns: colunasPorTabela[t] },
            position: {
              x: 100 + col * spacingX,
              y: 40 + row * spacingY,
            },
            style: { minWidth: minNodeWidth, minHeight: minNodeHeight },
            width: minNodeWidth,
            height: minNodeHeight,
            resizable: true
          };
        });

        setNodes(initialNodes);
        setLoading(false);
      });
  }, [user]);

  // nodeTypes injeta setNodes em cada node
  const nodeTypes = {
    tableNodeCustom: NodeWrapper(setNodes)
  };

  return (
    <div
      style={{
        width: "100vw",
        height: "92vh",
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
          borderRadius: 36,
          boxSizing: "border-box",
          position: "relative",
          boxShadow: "0 4px 32px #1976d224",
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
