import React, { useEffect, useState, useCallback } from "react";
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

// Componente da tabela customizada, com handles cobrindo toda a linha!
function TableNode({ data, selected }) {
  return (
    <div
      style={{
        background: "#fff",
        border: "2.5px solid #2284a1",
        borderRadius: 12,
        minWidth: 120,
        maxWidth: 440,
        minHeight: 28,
        boxShadow: "0 2px 16px #2284a128",
        padding: 4,
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
        minHeight={28}
        lineStyle={{ borderWidth: 2 }}
      />
      <div
        style={{
          fontWeight: 700,
          color: "#0B2132",
          marginBottom: 4,
          fontSize: 15,
          whiteSpace: "nowrap",
          textOverflow: "ellipsis",
          overflow: "hidden"
        }}
        title={data.label}
      >
        {data.label}
      </div>
      <div
        style={{
          maxHeight: "100%",
          overflowY: "auto",
          overflowX: "hidden"
        }}
      >
        {data.columns.map((col) => (
          <div
            key={col}
            style={{
              margin: "2px 0",
              padding: "2px 6px",
              borderRadius: 5,
              background: "#e4f3fa",
              fontSize: 12,
              position: "relative",
              whiteSpace: "nowrap",
              textOverflow: "ellipsis",
              overflow: "hidden",
              cursor: "crosshair"
            }}
            title={col}
          >
            {/* Handles cobrem toda a linha! */}
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
                borderRadius: 5,
                background: "rgba(0,0,0,0)",
                width: "100%",
                height: "100%",
                zIndex: 2,
                cursor: "crosshair"
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
                borderRadius: 5,
                background: "rgba(0,0,0,0)",
                width: "100%",
                height: "100%",
                zIndex: 2,
                cursor: "crosshair"
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

// Botão de auto-ajustar: força todos os nodes visíveis no viewport
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
        fitView({ nodes: allNodeIds, padding: 0.1, includeHiddenNodes: true });
      }}
    >
      Auto-ajustar
    </Button>
  );
}

function RelacionamentosVisualContent({ user }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [msg, setMsg] = useState({ open: false, text: "", severity: "success" });
  const [loading, setLoading] = useState(true);

  // Para autoajustar ao abrir:
  const { fitView, getNodes } = useReactFlow();

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

  // Ao terminar de carregar nodes, autoajusta todas as tabelas visíveis
  useEffect(() => {
    if (!loading && nodes.length) {
      setTimeout(() => {
        const allNodeIds = getNodes().map((n) => n.id);
        fitView({ nodes: allNodeIds, padding: 0.1, includeHiddenNodes: true });
      }, 120);
    }
  }, [loading, nodes, fitView, getNodes]);

  const onConnect = useCallback(
    async (params) => {
      const [tabela_origem, coluna_origem] = params.sourceHandle.split(".");
      const [tabela_destino, coluna_destino] = params.targetHandle.split(".");
      try {
        await api.post("/relacionamentos", {
          tabela_origem,
          coluna_origem,
          tabela_destino,
          coluna_destino,
          tipo_relacionamento: "1-N",
          empresa_id: user.empresa_id,
          email: user.email,
          senha: user.senha
        });
        setMsg({ open: true, text: "Relacionamento criado!", severity: "success" });
        setLoading(true);
        const relRes = await api.get("/relacionamentos", {
          params: { empresa_id: user.empresa_id, email: user.email, senha: user.senha }
        });
        const relacionamentos = relRes.data || [];
        const newEdges = relacionamentos.map((r) => ({
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
        setEdges(newEdges);
        setLoading(false);
      } catch {
        setMsg({ open: true, text: "Erro ao criar relacionamento.", severity: "error" });
      }
    },
    [user]
  );

  const onEdgeClick = useCallback(
    (event, edge) => {
      event.stopPropagation();
      if (window.confirm("Remover este relacionamento?")) {
        api
          .delete(`/relacionamentos/${edge.data.relId}`, {
            params: { email: user.email, senha: user.senha }
          })
          .then(() => {
            setMsg({ open: true, text: "Relacionamento removido!", severity: "success" });
            setEdges((eds) => eds.filter((e) => e.id !== edge.id));
          })
          .catch(() => setMsg({ open: true, text: "Erro ao remover relacionamento.", severity: "error" }));
      }
    },
    [user]
  );

  return (
    <Box sx={{ height: "calc(100vh - 60px)", width: "100vw", background: "#f8fafd", position: "relative" }}>
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
          fitView
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
          nodeDragBounds={{ left: 0, top: 0, right: 2200, bottom: 1100 }}
          extent="parent"
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
