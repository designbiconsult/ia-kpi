import React, { useRef, useState, useLayoutEffect } from "react";
import { Stage, Layer, Rect, Group, Text } from "react-konva";
import CropFreeIcon from "@mui/icons-material/CropFree";
import IconButton from "@mui/material/IconButton";

// Não some SIDEBAR_WIDTH, pois o App já faz isso!
const MIN_NODE_WIDTH = 150;
const MAX_NODE_WIDTH = 950;
const NODE_HEIGHT_BASE = 38;
const NODE_FIELD_HEIGHT = 30;

const tabelasFake = [
  { id: "Pedidos", campos: ["ID", "Data", "ClienteID", "Valor", "Status"] },
  { id: "Clientes", campos: ["ID", "Nome", "Cidade", "UF"] },
  { id: "Produtos", campos: ["ID", "Descrição", "Preço"] },
  { id: "Fornecedores", campos: ["ID", "RazãoSocial", "Cidade"] }
];

function getInitNodes() {
  // Agora x começa em 0, encostado na borda azul/Sidebar!
  return tabelasFake.map((t, idx) => ({
    id: t.id,
    x: 4 + (idx % 2) * 260, // 4px só de margem visual da borda
    y: 80 + Math.floor(idx / 2) * 210,
    width: 200,
    height: NODE_HEIGHT_BASE + t.campos.length * NODE_FIELD_HEIGHT,
    campos: t.campos,
    isDragging: false,
    isResizing: false
  }));
}

export default function RelacionamentosVisual() {
  const [canvasW, setCanvasW] = useState(window.innerWidth);
  const [canvasH, setCanvasH] = useState(window.innerHeight - 2);
  const [nodes, setNodes] = useState(() => getInitNodes());
  const resizingNode = useRef(null);

  useLayoutEffect(() => {
    const update = () => {
      setCanvasW(window.innerWidth);
      setCanvasH(window.innerHeight - 2);
    };
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  // Arraste: nunca passa da borda azul (esquerda = 0), nem sai pra direita
  const handleDragMove = (idx, e) => {
    let x = e.target.x();
    let y = e.target.y();
    const n = nodes[idx];
    // Limite esquerdo = borda azul (x=0)
    x = Math.max(4, x);
    // Limite direito: nunca ultrapassa a borda azul da direita
    x = Math.min(canvasW - n.width - 6, x);
    y = Math.max(0, Math.min(canvasH - n.height, y));
    e.target.x(x);
    e.target.y(y);
    setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, x, y } : n));
  };
  const handleDragStart = (idx) => setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, isDragging: true } : n));
  const handleDragEnd = (idx) => setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, isDragging: false } : n));

  // Só permite expandir para a DIREITA até a borda azul da direita
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
    // Limite direito: até a borda azul!
    const maxWidth = (canvasW - n.x - 6); // 6px de margem visual
    newWidth = Math.min(newWidth, maxWidth, MAX_NODE_WIDTH);
    setNodes((nds) => nds.map((node, i) => i === idx ? { ...node, width: newWidth } : node));
  };
  const handleResizeEnd = () => {
    resizingNode.current = null;
    setNodes((nds) => nds.map((n) => ({ ...n, isResizing: false })));
  };

  // Botão para ajustar viewport SEM centralizar tabelas!
  const stageRef = useRef();
  const handleFitView = () => {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(n => {
      minX = Math.min(minX, n.x);
      minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x + n.width);
      maxY = Math.max(maxY, n.y + n.height);
    });
    const pad = 30;
    minX = Math.max(minX - pad, 0);
    minY = Math.max(minY - pad, 0);
    maxX = Math.min(maxX + pad, canvasW);
    maxY = Math.min(maxY + pad, canvasH);
    const viewW = maxX - minX;
    const viewH = maxY - minY;
    const scaleX = canvasW / viewW;
    const scaleY = canvasH / viewH;
    const scale = Math.min(scaleX, scaleY, 1.0);
    stageRef.current?.to({
      x: -minX * scale,
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
      {/* Botão sempre visível, colado na borda azul */}
      <div style={{
        position: "absolute",
        top: 18,
        left: 18,
        zIndex: 10
      }}>
        <IconButton
          style={{
            border: "2px solid #1976d2",
            background: "#fff",
            borderRadius: 11,
            boxShadow: "0 2px 8px #1976d230"
          }}
          onClick={handleFitView}
          title="Ajustar visualização"
        >
          <CropFreeIcon sx={{ fontSize: 26, color: "#1976d2" }} />
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
        {/* Borda azul delimitadora */}
        <Layer>
          <Rect
            x={0}
            y={0}
            width={canvasW}
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
                shadowBlur={node.isDragging ? 15 : 8}
                shadowColor="#1976d2"
                stroke={node.isDragging || node.isResizing ? "#0B2132" : "#2284a1"}
                strokeWidth={node.isDragging || node.isResizing ? 3 : 2}
              />
              <Text
                text={node.id}
                x={15}
                y={11}
                fontSize={16.5}
                fontStyle="bold"
                fill="#1976d2"
                fontFamily="inherit"
                listening={false}
              />
              {node.campos.map((campo, cidx) => (
                <Text
                  key={campo}
                  text={campo}
                  x={18}
                  y={NODE_HEIGHT_BASE + cidx * (NODE_FIELD_HEIGHT - 2)}
                  fontSize={14.5}
                  fill="#444"
                  listening={false}
                  fontFamily="inherit"
                />
              ))}
              {/* Handle resize: só na DIREITA */}
              <Rect
                x={node.width - 11}
                y={10}
                width={15}
                height={node.height - 20}
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
      {/* Título fixo */}
      <div style={{
        position: "absolute", top: 12, left: 54, fontWeight: 700,
        fontSize: 20, color: "#1976d2", letterSpacing: 0.25, zIndex: 8
      }}>
        Relacionamentos Visual (Power BI Style)
      </div>
    </div>
  );
}
