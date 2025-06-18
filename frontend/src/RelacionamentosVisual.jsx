import React, { useRef, useState, useLayoutEffect } from "react";
import { Stage, Layer, Rect, Group, Text } from "react-konva";
import CropFreeIcon from "@mui/icons-material/CropFree";
import IconButton from "@mui/material/IconButton";

// Pegue a largura real do sidebar do seu app!
const SIDEBAR_WIDTH = 230; // igual ao drawerWidth do seu Sidebar.jsx

const MIN_NODE_WIDTH = 140;
const MAX_NODE_WIDTH = 800; // limite máximo da tabela
const NODE_HEIGHT_BASE = 35; // Altura inicial (título)
const NODE_FIELD_HEIGHT = 28; // Altura de cada campo

// Mock de tabelas. Integre com backend facilmente depois!
const tabelasFake = [
  { id: "Pedidos", campos: ["ID", "Data", "ClienteID", "Valor", "Status"] },
  { id: "Clientes", campos: ["ID", "Nome", "Cidade", "UF"] },
  { id: "Produtos", campos: ["ID", "Descrição", "Preço"] },
  { id: "Fornecedores", campos: ["ID", "RazãoSocial", "Cidade"] },
];

function getInitNodes(viewW) {
  // Espalha horizontalmente
  return tabelasFake.map((t, idx) => ({
    id: t.id,
    x: SIDEBAR_WIDTH + 40 + idx * 240,
    y: 70 + (idx % 2) * 220,
    width: 220,
    height: NODE_HEIGHT_BASE + t.campos.length * NODE_FIELD_HEIGHT,
    campos: t.campos,
    isDragging: false,
    isResizing: false,
  }));
}

export default function RelacionamentosKonva() {
  // Área de trabalho dinâmica!
  const [canvasW, setCanvasW] = useState(window.innerWidth - 2); // 2px para evitar scroll
  const [canvasH, setCanvasH] = useState(window.innerHeight - 80); // ajuste para o header
  const [nodes, setNodes] = useState(() => getInitNodes(window.innerWidth));
  const resizingNode = useRef(null);

  // Atualiza o tamanho do canvas ao redimensionar a janela!
  useLayoutEffect(() => {
    const updateSize = () => {
      setCanvasW(window.innerWidth - 2);
      setCanvasH(window.innerHeight - 80);
    };
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  // Drag: trava esquerda (SIDEBAR_WIDTH), deixa ir até a direita/bottom
  const handleDragMove = (idx, e) => {
    let x = e.target.x();
    let y = e.target.y();
    const n = nodes[idx];
    x = Math.max(SIDEBAR_WIDTH, Math.min(canvasW - n.width, x));
    y = Math.max(0, Math.min(canvasH - n.height, y));
    e.target.x(x);
    e.target.y(y);
    setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, x, y } : n));
  };

  // Drag Start/End
  const handleDragStart = (idx) => {
    setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, isDragging: true } : n));
  };
  const handleDragEnd = (idx) => {
    setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, isDragging: false } : n));
  };

  // Redimensionamento (resize só para a direita, nunca mexe no x)
  const handleResizeStart = (idx) => {
    resizingNode.current = idx;
    setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, isResizing: true } : n));
  };
  const handleResizeMove = (e) => {
    if (resizingNode.current === null) return;
    const idx = resizingNode.current;
    const n = nodes[idx];
    // Cálculo: diferença X mouse - X do node = nova largura
    let mouseX = e.target.getStage().getPointerPosition().x;
    let nextWidth = Math.max(MIN_NODE_WIDTH, mouseX - n.x);
    // Limite: nunca passar do canvas direito
    nextWidth = Math.min(nextWidth, canvasW - n.x - 2, MAX_NODE_WIDTH);
    setNodes((nds) => nds.map((node, i) => i === idx ? { ...node, width: nextWidth } : node));
  };
  const handleResizeEnd = () => {
    resizingNode.current = null;
    setNodes((nds) => nds.map((n) => ({ ...n, isResizing: false })));
  };

  // Auto-fit de viewport (zoom/scroll para mostrar tudo igual Power BI)
  const stageRef = useRef();
  const handleFitView = () => {
    // Calcula bounds de todas as tabelas
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(n => {
      minX = Math.min(minX, n.x);
      minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x + n.width);
      maxY = Math.max(maxY, n.y + n.height);
    });
    // Padding e ajuste visual
    const pad = 40;
    minX = Math.max(minX - pad, SIDEBAR_WIDTH);
    minY = Math.max(minY - pad, 0);
    maxX = Math.min(maxX + pad, canvasW);
    maxY = Math.min(maxY + pad, canvasH);
    // Calcula scale ideal
    const viewW = maxX - minX;
    const viewH = maxY - minY;
    const scaleX = canvasW / viewW;
    const scaleY = canvasH / viewH;
    const scale = Math.min(scaleX, scaleY, 1.0);
    // Aplica transform
    stageRef.current?.to({
      x: -minX * scale + SIDEBAR_WIDTH,
      y: -minY * scale,
      scaleX: scale,
      scaleY: scale,
      duration: 0.2,
    });
  };

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        background: "#f8fafd",
        margin: 0,
        padding: 0,
        overflow: "hidden"
      }}
    >
      {/* Botão de ajuste de zoom igual Power BI */}
      <div style={{ position: "absolute", top: 20, left: SIDEBAR_WIDTH + 14, zIndex: 10 }}>
        <IconButton
          style={{
            border: "2px solid #1976d2",
            background: "#fff",
            borderRadius: 10,
            boxShadow: "0 1px 10px #1976d23c",
          }}
          onClick={handleFitView}
          title="Ajustar visualização"
        >
          <CropFreeIcon sx={{ fontSize: 28, color: "#1976d2" }} />
        </IconButton>
      </div>
      <Stage
        ref={stageRef}
        width={canvasW}
        height={canvasH}
        style={{
          background: "#f8fafd",
          margin: 0,
          padding: 0,
          border: "none"
        }}
        onMouseMove={handleResizeMove}
        onMouseUp={handleResizeEnd}
      >
        {/* Delimitação visual do espaço útil */}
        <Layer>
          <Rect
            x={SIDEBAR_WIDTH}
            y={0}
            width={canvasW - SIDEBAR_WIDTH}
            height={canvasH}
            fill=""
            stroke="#1976d2"
            strokeWidth={6}
            dash={[16, 8]}
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
              onDragMove={(e) => handleDragMove(idx, e)}
              onDragEnd={() => handleDragEnd(idx)}
            >
              <Rect
                width={node.width}
                height={node.height}
                fill="#fff"
                cornerRadius={15}
                shadowBlur={node.isDragging ? 20 : 8}
                shadowColor="#2284a1"
                stroke={node.isDragging || node.isResizing ? "#0B2132" : "#2284a1"}
                strokeWidth={node.isDragging || node.isResizing ? 4 : 2}
              />
              <Text
                text={node.id}
                x={15}
                y={12}
                fontSize={19}
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
                  fontSize={15}
                  fill="#333"
                  listening={false}
                  fontFamily="inherit"
                />
              ))}
              {/* Handle de resize direito */}
              <Rect
                x={node.width - 8}
                y={8}
                width={14}
                height={node.height - 16}
                fill={node.isResizing ? "#0B2132" : "#2284a1"}
                opacity={0.60}
                cornerRadius={7}
                draggable={false}
                onMouseDown={() => handleResizeStart(idx)}
                style={{ cursor: "ew-resize" }}
              />
            </Group>
          ))}
        </Layer>
      </Stage>
      {/* Título/Legenda */}
      <div
        style={{
          position: "absolute",
          top: 14,
          left: SIDEBAR_WIDTH + 80,
          fontWeight: 700,
          fontSize: 22,
          color: "#1976d2",
          letterSpacing: 0.5,
          zIndex: 5,
        }}
      >
        Relacionamentos Visual (Power BI UX)
      </div>
    </div>
  );
}
