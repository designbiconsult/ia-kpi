import React, { useRef, useEffect, useState, useCallback } from "react";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  NodeResizer,
  useReactFlow,
  ReactFlowProvider
} from "reactflow";
import "reactflow/dist/style.css";
import { Alert, Snackbar, Box, Button, CircularProgress } from "@mui/material";

function TableNode({ data, selected }) {
  return (
    <div
      style={{
        background: "#fff",
        border: "2.5px solid #2284a1",
        borderRadius: 14,
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
      <div style={{ maxHeight: 300, overflowY: "auto" }}>
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
              cursor: "crosshair"
            }}
            title={col}
          >
            <Handle
              type="source"
              id={`${data.label}.${col}`}
              position={Position.Right}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                width: "100%",
                height: "100%",
                zIndex: 2,
                cursor: "crosshair",
                background: "rgba(0,0,0,0)"
              }}
            />
            <Handle
              type="target"
              id={`${data.label}.${col}`}
              position={Position.Left}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                width: "100%",
                height: "100%",
                zIndex: 2,
                cursor: "crosshair",
                background: "rgba(0,0,0,0)"
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

function AutoFitButton() {
  const { fitView, getNodes } = useReactFlow();
  return (
    <Button
      variant="contained"
      sx={{
        position: "absolute",
        zIndex: 12,
        top: 14,
        left: 250,
        bgcolor: "#0B2132",
        fontWeight: 700,
        "&:hover": { bgcolor: "#06597a" }
      }}
      onClick={() => {
        const allNodeIds = getNodes().map((n) => n.id);
        fitView({ nodes: allNodeIds, padding: 0.15, includeHiddenNodes: true });
      }}
    >
      Auto-ajustar
    </Button>
  );
}

function RelacionamentosVisualContent({ user, api, tabelasDemo, colunasDemo, edgesDemo }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [msg, setMsg] = useState({ open: false, text: "", severity: "success" });
  const [loading, setLoading] = useState(true);

  const containerRef = useRef();
  const [dragBounds, setDragBounds] = useState({
    left: 0,
    top: 0,
    right: 0,
    bottom: 0
  });

  const { fitView, getNodes, setViewport } = useReactFlow();

  useEffect(() => {
    function updateBounds() {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDragBounds({
          left: 10, // padding igual Power BI
          top: 10,
          right: rect.width - 10,
          bottom: rect.height - 10
        });
      }
    }
    updateBounds();
    window.addEventListener("resize", updateBounds);
    return () => window.removeEventListener("resize", updateBounds);
  }, []);

  useEffect(() => {
    // Use dados demo para simular Power BI
    if (tabelasDemo && colunasDemo && edgesDemo) {
      const initialNodes = tabelasDemo.map((t, idx) => ({
        id: t,
        type: "table",
        data: { label: t, columns: colunasDemo[t] || [] },
        position: { x: 100 + 260 * (idx % 4), y: 60 + 220 * Math.floor(idx / 4) },
        style: { minWidth: 120, minHeight: 36 },
        resizable: true
      }));
      setNodes(initialNodes);
      setEdges(edgesDemo);
      setLoading(false);
    }
  }, [tabelasDemo, colunasDemo, edgesDemo]);

  // Auto-fit ao montar
  useEffect(() => {
    if (!loading && nodes.length) {
      setTimeout(() => {
        const allNodeIds = getNodes().map((n) => n.id);
        fitView({ nodes: allNodeIds, padding: 0.13, includeHiddenNodes: true });
      }, 140);
    }
  }, [loading, nodes, fitView, getNodes]);

  // Bloquear pan além do canvas (Power BI style)
  const onMove = useCallback((e, viewport) => {
  if (containerRef.current) {
    let { x, y } = viewport;
    let changed = false;
    if (x > 0) { x = 0; changed = true; }
    if (y > 0) { y = 0; changed = true; }
    if (changed) setViewport({ x, y, zoom: viewport.zoom });
  }
}, [setViewport]);


  return (
    <Box
      ref={containerRef}
      sx={{
        height: "calc(100vh - 60px)",
        width: "100vw",
        background: "#f8fafd",
        position: "relative",
        overflow: "hidden"
      }}
    >
      {loading && (
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "70vh" }}>
          <CircularProgress size={32} sx={{ mr: 2 }} />
          <span style={{ fontSize: 20 }}>Carregando tabelas...</span>
        </Box>
      )}
      {!loading && (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          minZoom={0.2}
          maxZoom={2.2}
          panOnDrag
          nodesDraggable
          nodesConnectable
          edgesFocusable
          elevateNodesOnSelect
          defaultEdgeOptions={{ type: "smoothstep" }}
          proOptions={{ hideAttribution: true }}
          nodeDragBounds={dragBounds}
          onMove={onMove}
        >
          <MiniMap nodeColor={() => "#2284a1"} />
          <Controls />
          <Background color="#dde7f2" gap={32} />
          <AutoFitButton />
        </ReactFlow>
      )}
      <Snackbar
        open={msg.open}
        autoHideDuration={3200}
        onClose={() => setMsg((m) => ({ ...m, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={msg.severity} variant="filled">
          {msg.text}
        </Alert>
      </Snackbar>
    </Box>
  );
}

// Simulação de dados igual ao Power BI
const tabelasDemo = ["Pedidos", "Clientes", "Produtos", "Notas"];
const colunasDemo = {
  Pedidos: ["ID", "Data", "ID_Cliente", "Valor", "Status"],
  Clientes: ["ID", "Nome", "Cidade", "UF"],
  Produtos: ["ID", "Nome", "Preço", "Estoque"],
  Notas: ["ID", "ID_Pedido", "Data", "Total"]
};
const edgesDemo = [
  {
    id: "e1",
    source: "Pedidos",
    sourceHandle: "Pedidos.ID_Cliente",
    target: "Clientes",
    targetHandle: "Clientes.ID",
    label: "1-N",
    style: { stroke: "#0B2132" },
    animated: true,
    data: { relId: 1 }
  },
  {
    id: "e2",
    source: "Notas",
    sourceHandle: "Notas.ID_Pedido",
    target: "Pedidos",
    targetHandle: "Pedidos.ID",
    label: "N-1",
    style: { stroke: "#2284a1" },
    animated: true,
    data: { relId: 2 }
  }
];

// PRONTO PARA TESTAR, igual ao Power BI:
export default function RelacionamentosVisual() {
  return (
    <ReactFlowProvider>
      <RelacionamentosVisualContent
        tabelasDemo={tabelasDemo}
        colunasDemo={colunasDemo}
        edgesDemo={edgesDemo}
      />
    </ReactFlowProvider>
  );
}
