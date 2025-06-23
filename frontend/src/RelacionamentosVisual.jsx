import React, { useRef, useState, useLayoutEffect } from "react";
import { Stage, Layer, Rect, Group, Text } from "react-konva";
import CropFreeIcon from "@mui/icons-material/CropFree";
import IconButton from "@mui/material/IconButton";

const MIN_NODE_WIDTH = 150;
const MAX_NODE_WIDTH = 950;
const NODE_HEIGHT_BASE = 38;
const NODE_FIELD_HEIGHT = 30;
const PADDING = 220; // Espaço extra à direita e embaixo

const tabelasFake = [
  { id: "Pedidos", campos: ["ID", "Data", "ClienteID", "Valor", "Status"] },
  { id: "Clientes", campos: ["ID", "Nome", "Cidade", "UF"] },
  { id: "Produtos", campos: ["ID", "Descrição", "Preço"] },
  { id: "Fornecedores", campos: ["ID", "RazãoSocial", "Cidade"] }
];

function getInitNodes() {
  return tabelasFake.map((t, idx) => ({
    id: t.id,
    x: 4 + (idx % 2) * 260,
    y: 80 + Math.floor(idx / 2) * 210,
    width: 200,
    height: NODE_HEIGHT_BASE + t.campos.length * NODE_FIELD_HEIGHT,
    campos: t.campos,
    isDragging: false,
    isResizing: false
  }));
}

export default function RelacionamentosVisual() {
  const [nodes, setNodes] = useState(() => getInitNodes());
  const resizingNode = useRef(null);

  // Calcula dinamicamente a largura e altura do Stage com base nas tabelas
  const [canvasSize, setCanvasSize] = useState({ width: window.innerWidth, height: window.innerHeight - 2 });

  // Sempre que nodes mudam, recalcula o tamanho do Stage
  useLayoutEffect(() => {
    let maxRight = 0, maxBottom = 0;
    nodes.forEach((n) => {
      maxRight = Math.max(maxRight, n.x + n.width);
      maxBottom = Math.max(maxBottom, n.y + n.height);
    });
    setCanvasSize({
      width: Math.max(window.innerWidth, maxRight + PADDING),
      height: Math.max(window.innerHeight - 2, maxBottom + PADDING)
    });
  }, [nodes]);

  // Arraste: nunca passa da borda esquerda (x=0)
  const handleDragMove = (idx, e) => {
    let x = e.target.x();
    let y = e.target.y();
    const n = nodes[idx];
    x = Math.max(4, x); // margem esquerda
    y = Math.max(0, y); // margem topo
    e.target.x(x);
    e.target.y(y);
    setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, x, y } : n));
  };
  const handleDragStart = (idx) => setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, isDragging: true } : n));
  const handleDragEnd = (idx) => setNodes((nds) => nds.map((n, i) => i === idx ? { ...n, isDragging: false } : n));

  // Permite expandir para a direita livre, Stage cresce automaticamente!
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
    // Deixa a tabela crescer até MAX_NODE_WIDTH (ou mais, se quiser)
    newWidth = Math.min(newWidth, MAX_NODE_WIDTH);
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
    maxX = Math.min(maxX + pad, canvasSize.width);
    maxY = Math.min(maxY + pad, canvasSize.height);
    const viewW = maxX - minX;
    const viewH = maxY - minY;
    const scaleX = window.innerWidth / viewW;
    const scaleY = window.innerHeight / viewH;
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
    <div
      style={{
        width: "100vw",
        height: "100vh",
        background: "#f8fafd",
        margin: 0,
        padding: 0,
        // O segredo está aqui:
        overflow: "auto",
        minWidth: "100vw"
      }}
    >
      {/* Botão sempre visível */}
      <div
        style={{
          position: "fixed",
          top: 18,
          left: 18,
          zIndex: 10
        }}
      >
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
        width={canvasSize.width}
        height={canvasSize.height}
        style={{
          background: "#f8fafd",
          margin: 0,
          padding: 0,
          border: "none",
          display: "block"
        }}
        onMouseMove={handleResizeMove}
        onMouseUp={handleResizeEnd}
      >
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
      <div
        style={{
          position: "fixed",
          top: 12,
          left: 54,
          fontWeight: 700,
          fontSize: 20,
          color: "#1976d2",
          letterSpacing: 0.25,
          zIndex: 8
        }}
      >
        Relacionamentos Visual (Power BI Style)
      </div>
    </div>
  );
}
