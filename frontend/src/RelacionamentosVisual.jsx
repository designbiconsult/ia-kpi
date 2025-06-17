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
import { api } from "./api";
import { Alert, Snackbar, Box, Button, CircularProgress } from "@mui/material";

// ... TableNode igual ao exemplo anterior ...

function RelacionamentosVisualContent({ user }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [msg, setMsg] = useState({ open: false, text: "", severity: "success" });
  const [loading, setLoading] = useState(true);

  const containerRef = useRef();
  const [dragBounds, setDragBounds] = useState({ left: 0, top: 0, right: 0, bottom: 0 });

  const { fitView, getNodes } = useReactFlow();

  // Atualiza os limites do drag sempre que o tamanho da tela muda
  useEffect(() => {
    function updateBounds() {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDragBounds({
          left: 0,
          top: 0,
          right: rect.width,
          bottom: rect.height,
        });
      }
    }
    updateBounds();
    window.addEventListener("resize", updateBounds);
    return () => window.removeEventListener("resize", updateBounds);
  }, []);

  useEffect(() => {
    if (!user || !user.empresa_id) return;
    setLoading(true);
    Promise.all([
      api.get("/tabelas/listar", { params: { empresa_id: user.empresa_id } }),
      api.get("/relacionamentos", {
        params: { empresa_id: user.empresa_id, email: user.email, senha: user.senha }
      })
    ])
      .then(async ([tabRes, relRes]) => {
        const tabelas = tabRes.data || [];
        const relacionamentos = relRes.data || [];
        const colunasPorTabela = {};
        await Promise.all(
          tabelas.map(async (t) => {
            const resp = await api.get("/tabelas/colunas", { params: { tabela: t } });
            colunasPorTabela[t] = resp.data || [];
          })
        );
        const initialNodes = tabelas.map((t, idx) => ({
          id: t,
          type: "table",
          data: { label: t, columns: colunasPorTabela[t] },
          position: { x: 80 + 200 * (idx % 6), y: 30 + 120 * Math.floor(idx / 6) },
          style: { minWidth: 120, minHeight: 28 },
          resizable: true,
        }));
        const initialEdges = (relacionamentos || []).map((r) => ({
          id: `e-${r.id}`,
          source: r.tabela_origem,
          sourceHandle: `${r.tabela_origem}.${r.coluna_origem}`,
          target: r.tabela_destino,
          targetHandle: `${r.tabela_destino}.${r.coluna_destino}`,
          animated: true,
          label: r.tipo_relacionamento,
          style: { stroke: "#0B2132" },
          data: { relId: r.id }
        }));

        setNodes(initialNodes);
        setEdges(initialEdges);
        setLoading(false);
      })
      .catch(() => {
        setMsg({
          open: true,
          text: "Erro ao carregar tabelas/relacionamentos.",
          severity: "error"
        });
        setLoading(false);
      });
  }, [user]);

  useEffect(() => {
    if (!loading && nodes.length) {
      setTimeout(() => {
        const allNodeIds = getNodes().map((n) => n.id);
        fitView({ nodes: allNodeIds, padding: 0.1, includeHiddenNodes: true });
      }, 120);
    }
  }, [loading, nodes, fitView, getNodes]);

  // ...onConnect e onEdgeClick igual...

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
          onConnect={onConnect}
          onEdgeClick={onEdgeClick}
          nodeTypes={nodeTypes}
          minZoom={0.1}
          maxZoom={2.2}
          panOnDrag
          nodesDraggable
          nodesConnectable
          edgesFocusable
          elevateNodesOnSelect
          defaultEdgeOptions={{ type: "smoothstep" }}
          proOptions={{ hideAttribution: true }}
          nodeDragBounds={dragBounds}
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

export default function RelacionamentosVisual(props) {
  return (
    <ReactFlowProvider>
      <RelacionamentosVisualContent {...props} />
    </ReactFlowProvider>
  );
}
