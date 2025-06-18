import React, { useRef, useState, useLayoutEffect } from "react";
import { Stage, Layer, Rect, Group, Text } from "react-konva";
import CropFreeIcon from "@mui/icons-material/CropFree";
import IconButton from "@mui/material/IconButton";

// Altere aqui se seu sidebar tiver largura diferente!
const SIDEBAR_WIDTH = 230;

const MIN_NODE_WIDTH = 150;
const MAX_NODE_WIDTH = 750;
const NODE_HEIGHT_BASE = 38;
const NODE_FIELD_HEIGHT = 30;

// Exemplo (depois puxe do backend)
const tabelasFake = [
  { id: "Pedidos", campos: ["ID", "Data", "ClienteID", "Valor", "Status"] },
  { id: "Clientes", campos: ["ID", "Nome", "Cidade", "UF"] },
  { id: "Produtos", campos: ["ID", "Descrição", "Preço"] },
  { id: "Fornecedores", campos: ["ID", "RazãoSocial", "Cidade"] }
];

// Gera nodes espaçados horizontalmente a partir da borda azul (sem espaço sobrando)
function getInitNodes(viewW) {
  return tabelasFake.map((t, idx) => ({
    id: t.id,
    x: SIDEBAR_WIDTH + 32 + (idx % 2) * 350,
    y: 90 + Math.floor(idx / 2) * 220,
    width: 210,
    height: NODE_HEIGHT_BASE + t.campos.length * NODE_FIELD_HEIGHT,
    campos: t.campos,
    isDragging: false,
    isResizing: false
  }));
}

export default function RelacionamentosVisual() {
  // Agora 100% dinâmico, sem espaço em branco!
  const [canvasW, setCanvasW] = useState(window.innerWidth);
  const [canvasH, setCanvasH] = useState(window.innerHeight - 2);
  const [nodes, setNodes] = useState(() => getInitNodes(window.innerWidth));
  const resizingNode = useRef(null);

  // Responsividade: ajusta ao redimensionar
  useLayoutEffect(() => {
    const update = () => {
      setCanvasW(window.innerWidth);
      setCanvasH(window.innerHeight - 2);
    };
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  // Arraste: nunca passa da borda azul
  const handleDragMove = (idx, e) => {
    let x = e.target.x();
    let y = e.target.y();
    const n = nodes[idx];
    // Limite esquerdo: borda azul (sidebar)
    x = Math.max(SIDEBAR_WIDTH, x);
    // Limite direito: nunca sair do canvas
    x = Math.min(canvasW - n.width, x);
    y = Math.max(0, Math.min(canvasH - n.height, y));
    e.target.x(x);
    e.target.y(y);
    setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, x, y } : n));
  };
  const handleDragStart = (idx) => setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, isDragging: true } : n));
  const handleDragEnd = (idx) => setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, isDragging: false } : n));

  // Redimensiona para a direita, nunca para esquerda!
  const handleResizeStart = (idx) => {
    resizingNode.current = idx;
    setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, isResizing: true } : n));
  };
  const handleResizeMove = (e) => {
    if (resizingNode.current === null) return;
    const idx = resizingNode.current;
    const n = nodes[idx];
    let mouseX = e.target.getStage().getPointerPosition().x;
    let newWidth = Math.max(MIN_NODE_WIDTH, mouseX - n.x);
    newWidth = Math.min(newWidth, canvasW - n.x - 8, MAX_NODE_WIDTH);
    setNodes((nds) => nds.map((node, i) => i === idx ? { ...node, width: newWidth } : node));
  };
  const handleResizeEnd = () => {
    resizingNode.current = null;
    setNodes((nds) => nds.map((n) => ({ ...n, isResizing: false })));
  };

  // Botão "ajustar visualização": coloca tudo no viewport!
  const stageRef = useRef();
  const handleFitView = () => {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(n => {
      minX = Math.min(minX, n.x);
      minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x + n.width);
      maxY = Math.max(maxY, n.y + n.height);
    });
    const pad = 40;
    minX = Math.max(minX - pad, SIDEBAR_WIDTH);
    minY = Math.max(minY - pad, 0);
    maxX = Math.min(maxX + pad, canvasW);
    maxY = Math.min(maxY + pad, canvasH);
    const viewW = maxX - minX;
    const viewH = maxY - minY;
    const scaleX = (canvasW - SIDEBAR_WIDTH) / viewW;
    const scaleY = canvasH / viewH;
    const scale = Math.min(scaleX, scaleY, 1.0);
    stageRef.current?.to({
      x: -minX * scale + SIDEBAR_WIDTH,
      y: -minY * scale,
      scaleX: scale,
      scaleY: scale,
      duration: 0.2
    });
  };

  return (
    <div style={{
      width: "100vw", height: "100vh",
      background: "#f8fafd",
      margin: 0, padding: 0, overflow: "hidden"
    }}>
      {/* Botão aparece sempre, colado na borda azul! */}
      <div style={{
        position: "absolute",
        top: 20, left: SIDEBAR_WIDTH + 16, zIndex: 10
      }}>
        <IconButton
          style={{
            border: "2px solid #1976d2",
            background: "#fff",
            borderRadius: 12,
            boxShadow: "0 2px 10px #1976d233"
          }}
          onClick={handleFitView}
          title="Ajustar visualização"
        >
          <CropFreeIcon sx={{ fontSize: 30, color: "#1976d2" }} />
        </IconButton>
      </div>
      <Stage
        ref={stageRef}
        width={canvasW}
        height={canvasH}
        style={{ background: "#f8fafd", margin: 0, padding: 0, border: "none" }}
        onMouseMove={handleResizeMove}
        onMouseUp={handleResizeEnd}
      >
        {/* Delimita o espaço azul, SEM margem */}
        <Layer>
          <Rect
            x={SIDEBAR_WIDTH}
            y={0}
            width={canvasW - SIDEBAR_WIDTH}
            height={canvasH}
            fill=""
            stroke="#1976d2"
            strokeWidth={6}
            dash={[18, 9]}
            listening={false}
          />
        </Layer>
        <Layer>
          {nodes.map((node, idx) => (
            <Group
              key={node.id}
              x={node.x}
              y={node.y}
              draggable={!node.isResizing}
              onDragStart={() => handleDragStart(idx)}
              onDragMove={e => handleDragMove(idx, e)}
              onDragEnd={() => handleDragEnd(idx)}
            >
              <Rect
                width={node.width}
                height={node.height}
                fill="#fff"
                cornerRadius={13}
                shadowBlur={node.isDragging ? 16 : 9}
                shadowColor="#1976d2"
                stroke={node.isDragging || node.isResizing ? "#0B2132" : "#2284a1"}
                strokeWidth={node.isDragging || node.isResizing ? 3.5 : 2}
              />
              <Text
                text={node.id}
                x={14}
                y={12}
                fontSize={18}
                fontStyle="bold"
                fill="#1976d2"
                fontFamily="inherit"
                listening={false}
              />
              {node.campos.map((campo, cidx) => (
                <Text
                  key={campo}
                  text={campo}
                  x={20}
                  y={NODE_HEIGHT_BASE + cidx * (NODE_FIELD_HEIGHT - 2)}
                  fontSize={15.2}
                  fill="#444"
                  listening={false}
                  fontFamily="inherit"
                />
              ))}
              {/* Handle resize só na DIREITA */}
              <Rect
                x={node.width - 10}
                y={9}
                width={14}
                height={node.height - 18}
                fill={node.isResizing ? "#0B2132" : "#2284a1"}
                opacity={0.60}
                cornerRadius={6}
                draggable={false}
                onMouseDown={() => handleResizeStart(idx)}
                style={{ cursor: "ew-resize" }}
              />
            </Group>
          ))}
        </Layer>
      </Stage>
      {/* Título fixo, colado no topo */}
      <div style={{
        position: "absolute", top: 10, left: SIDEBAR_WIDTH + 70, fontWeight: 700,
        fontSize: 21, color: "#1976d2", letterSpacing: 0.3, zIndex: 8
      }}>
        Relacionamentos Visual (Power BI Style)
      </div>
    </div>
  );
}
