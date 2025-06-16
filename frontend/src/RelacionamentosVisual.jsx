import React, { useEffect, useState, useCallback } from "react";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  addEdge,
  useNodesState,
  useEdgesState,
  Handle,
  Position
} from "reactflow";
import "reactflow/dist/style.css";
import { api } from "./api";
import { Alert, Snackbar } from "@mui/material";

const edgeTypes = {};
const nodeTypes = {};

function TableNode({ data }) {
  // data: { label, columns }
  return (
    <div style={{
      background: "#fff",
      border: "2px solid #2284a1",
      borderRadius: 8,
      minWidth: 170,
      padding: 8,
      boxShadow: "0 2px 8px #aaa2"
    }}>
      <div style={{ fontWeight: 700, color: "#2284a1", marginBottom: 8 }}>{data.label}</div>
      <div>
        {data.columns.map((col, i) => (
          <div key={col} style={{
            margin: "3px 0", padding: "2px 6px", borderRadius: 4,
            background: "#e6f0fa", fontSize: 14, position: "relative"
          }}>
            {/* Handle para criar conexões */}
            <Handle
              type="source"
              id={`${data.label}.${col}`}
              position={Position.Right}
              style={{ right: -8, background: "#0B2132", width: 8, height: 8 }}
            />
            <Handle
              type="target"
              id={`${data.label}.${col}`}
              position={Position.Left}
              style={{ left: -8, background: "#0B2132", width: 8, height: 8 }}
            />
            {col}
          </div>
        ))}
      </div>
    </div>
  );
}

nodeTypes.table = TableNode;

export default function RelacionamentosVisual({ user }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [msg, setMsg] = useState({ open: false, text: "", severity: "success" });
  const [loading, setLoading] = useState(true);

  // Carregar tabelas e relacionamentos
  useEffect(() => {
    if (!user || !user.empresa_id) return;
    setLoading(true);
    Promise.all([
      api.get("/tabelas/listar", { params: { empresa_id: user.empresa_id } }),
      api.get("/relacionamentos", { params: { empresa_id: user.empresa_id, email: user.email, senha: user.senha } }),
      // Busca as colunas de todas as tabelas
    ]).then(async ([tabRes, relRes]) => {
      const tabelas = tabRes.data || [];
      const relacionamentos = relRes.data || [];

      // Buscar as colunas de cada tabela
      const colunasPorTabela = {};
      await Promise.all(
        tabelas.map(async t => {
          const resp = await api.get("/tabelas/colunas", { params: { tabela: t } });
          colunasPorTabela[t] = resp.data || [];
        })
      );

      // Distribui as tabelas na tela automaticamente
      const initialNodes = tabelas.map((t, idx) => ({
        id: t,
        type: "table",
        data: { label: t, columns: colunasPorTabela[t] },
        position: { x: 120 + 250 * (idx % 3), y: 60 + 220 * Math.floor(idx / 3) }
      }));

      // Cria edges a partir dos relacionamentos
      const initialEdges = (relacionamentos || []).map(r => ({
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
    }).catch(() => {
      setMsg({ open: true, text: "Erro ao carregar tabelas/relacionamentos.", severity: "error" });
      setLoading(false);
    });
    // eslint-disable-next-line
  }, [user]);

  // Ao criar uma nova conexão com o mouse
  const onConnect = useCallback(
    async (params) => {
      // params: { source, sourceHandle, target, targetHandle }
      // sourceHandle/targetHandle = "tabela.coluna"
      const [tabela_origem, coluna_origem] = params.sourceHandle.split(".");
      const [tabela_destino, coluna_destino] = params.targetHandle.split(".");

      // (Opcional: abrir um dialog para escolher tipo 1-1, 1-N, N-N)
      // Aqui padrão como 1-N:
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
        // Refaz edges (recarrega do backend)
        // Dica: poderíamos otimizar, mas preferi sempre pegar do backend para não ter bug
        setLoading(true);
        const relRes = await api.get("/relacionamentos", { params: { empresa_id: user.empresa_id, email: user.email, senha: user.senha } });
        const relacionamentos = relRes.data || [];
        const newEdges = relacionamentos.map(r => ({
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

  // Remover relacionamento (ao clicar na linha)
  const onEdgeClick = useCallback(
    (event, edge) => {
      event.stopPropagation();
      if (window.confirm("Remover este relacionamento?")) {
        api.delete(`/relacionamentos/${edge.data.relId}`, {
          params: { email: user.email, senha: user.senha }
        }).then(() => {
          setMsg({ open: true, text: "Relacionamento removido!", severity: "success" });
          setEdges(eds => eds.filter(e => e.id !== edge.id));
        }).catch(() => setMsg({ open: true, text: "Erro ao remover relacionamento.", severity: "error" }));
      }
    },
    [user]
  );

  return (
    <div style={{ height: "calc(100vh - 50px)", background: "#f8fafd", minWidth: "100vw" }}>
      {loading && <div style={{ padding: 60, fontSize: 22 }}>Carregando tabelas...</div>}
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
          edgeTypes={edgeTypes}
        >
          <MiniMap nodeColor={() => "#2284a1"} />
          <Controls />
          <Background color="#e4f3fa" gap={18} />
        </ReactFlow>
      )}
      <Snackbar
        open={msg.open}
        autoHideDuration={3200}
        onClose={() => setMsg(m => ({ ...m, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={msg.severity} variant="filled">{msg.text}</Alert>
      </Snackbar>
    </div>
  );
}
