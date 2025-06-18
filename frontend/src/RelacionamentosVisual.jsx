import React, { useRef, useState } from "react";
import { Stage, Layer, Rect, Group, Text } from "react-konva";
import CropFreeIcon from "@mui/icons-material/CropFree"; // Botão de autoajuste (opcional)
import IconButton from "@mui/material/IconButton";

// CONFIGURE AQUI conforme sua sidebar/menu lateral!
const SIDEBAR_OFFSET = 230; // <<--- LARGURA EXATA DO DRAWER
const CANVAS_W = 1700 + SIDEBAR_OFFSET; // <<--- Largura total incluindo offset
const CANVAS_H = 900;
const MIN_WIDTH = 140;
const MAX_WIDTH = 600;
const MIN_HEIGHT = 45;

// Exemplo de tabelas
const tabelasFake = [
  { id: "Pedidos", campos: ["ID", "Data", "ClienteID", "Valor", "Status"] },
  { id: "Clientes", campos: ["ID", "Nome", "Cidade", "UF"] },
  { id: "Produtos", campos: ["ID", "Descrição", "Preço"] },
  { id: "Fornecedores", campos: ["ID", "RazãoSocial", "Cidade"] },
];

function getInitNodes() {
  return tabelasFake.map((t, idx) => ({
    id: t.id,
    x: SIDEBAR_OFFSET + 30 + idx * 260,
    y: 80 + (idx % 2) * 220,
    width: 220,
    height: Math.max(MIN_HEIGHT, 35 + t.campos.length * 28),
    campos: t.campos,
    isDragging: false,
    isResizing: false,
  }));
}

export default function RelacionamentosKonva() {
  const [nodes, setNodes] = useState(getInitNodes());
  const resizingNode = useRef(null);

  // Handler de arrasto (trava só na ESQUERDA)
  const handleDragMove = (idx, e) => {
    let x = e.target.x();
    let y = e.target.y();
    // Limite ESQUERDA = SIDEBAR, DIREITA = canvas - node.width
    x = Math.max(SIDEBAR_OFFSET, Math.min(CANVAS_W - nodes[idx].width, x));
    y = Math.max(0, Math.min(CANVAS_H - nodes[idx].height, y));
    e.target.x(x);
    e.target.y(y);
    setNodes((nds) =>
      nds.map((n, i) =>
        i === idx ? { ...n, x, y } : n
      )
    );
  };

  // Drag Start/End
  const handleDragStart = (idx) => {
    setNodes((nds) =>
      nds.map((n, i) =>
        i === idx ? { ...n, isDragging: true } : n
      )
    );
  };
  const handleDragEnd = (idx) => {
    setNodes((nds) =>
      nds.map((n, i) =>
        i === idx ? { ...n, isDragging: false } : n
      )
    );
  };

  // Resize só pela direita (NUNCA deixa crescer para a esquerda, mas direita é ilimitado)
  const handleResizeStart = (idx) => {
    resizingNode.current = idx;
    setNodes((nds) =>
      nds.map((n, i) =>
        i === idx ? { ...n, isResizing: true } : n
      )
    );
  };

  const handleResizeMove = (e) => {
    if (resizingNode.current === null) return;
    const idx = resizingNode.current;
    const n = nodes[idx];
    // x mouse relativo ao node
    let nextWidth = Math.max(MIN_WIDTH, e.evt.layerX - n.x);
    // Não deixa crescer para a esquerda
    if (nextWidth < MIN_WIDTH) nextWidth = MIN_WIDTH;
    // Cresce até o limite do canvas (opcional) - ou retire para deixar livre
    if (n.x + nextWidth > CANVAS_W) nextWidth = CANVAS_W - n.x - 2;
    // Não limita a direita a não ser que bata no limite do canvas
    setNodes((nds) =>
      nds.map((node, i) =>
        i === idx ? { ...node, width: nextWidth } : node
      )
    );
  };

  const handleResizeEnd = () => {
    resizingNode.current = null;
    setNodes((nds) =>
      nds.map((n) => ({ ...n, isResizing: false }))
    );
  };

  // Autoajuste (centraliza todas as tabelas no espaço do canvas)
  const handleAutoFit = () => {
    // Calcula bounds das tabelas
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach((n) => {
      minX = Math.min(minX, n.x);
      minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x + n.width);
      maxY = Math.max(maxY, n.y + n.height);
    });
    // Calcula espaço disponível
    const areaW = CANVAS_W - SIDEBAR_OFFSET - 60;
    const areaH = CANVAS_H - 40;
    const widthTabelas = maxX - minX;
    const heightTabelas = maxY - minY;
    // Padding top/left para centralizar
    const padX = Math.max(SIDEBAR_OFFSET + 20, SIDEBAR_OFFSET + (areaW - widthTabelas) / 2);
    const padY = Math.max(20, (areaH - heightTabelas) / 2);
    // Move todas para ficarem centralizadas
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        x: padX + (n.x - minX),
        y: padY + (n.y - minY),
      }))
    );
  };

  return (
    <div
      style={{
        width: CANVAS_W,
        background: "#e4f3fa",
        borderRadius: 24,
        boxShadow: "0 6px 38px #1976d218",
        border: "6px solid #1976d2",
        position: "relative",
        marginLeft: 0, // encostado na lateral
        overflow: "hidden",
      }}
    >
      {/* Botão de auto-ajuste */}
      <div style={{ position: "absolute", top: 12, left: SIDEBAR_OFFSET + 16, zIndex: 10 }}>
        <IconButton
          style={{
            border: "2px solid #1976d2",
            background: "#fff",
            borderRadius: 10,
            boxShadow: "0 1px 10px #1976d23c",
          }}
          onClick={handleAutoFit}
          title="Ajustar tudo"
        >
          <CropFreeIcon sx={{ fontSize: 28, color: "#1976d2" }} />
        </IconButton>
      </div>
      <Stage
        width={CANVAS_W}
        height={CANVAS_H}
        style={{
          borderRadius: 18,
          background: "#f8fafd",
          marginLeft: 0,
        }}
        onMouseMove={handleResizeMove}
        onMouseUp={handleResizeEnd}
      >
        {/* Delimitação visual */}
        <Layer>
          <Rect
            x={SIDEBAR_OFFSET}
            y={0}
            width={CANVAS_W - SIDEBAR_OFFSET}
            height={CANVAS_H}
            fill=""
            stroke="#1976d2"
            strokeWidth={5}
            dash={[14, 10]}
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
                cornerRadius={16}
                shadowBlur={node.isDragging ? 20 : 7}
                shadowColor="#2284a1"
                stroke={node.isDragging || node.isResizing ? "#0B2132" : "#2284a1"}
                strokeWidth={node.isDragging || node.isResizing ? 4 : 2}
              />
              <Text
                text={node.id}
                x={15}
                y={11}
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
                  y={35 + cidx * 26}
                  fontSize={15}
                  fill="#333"
                  listening={false}
                  fontFamily="inherit"
                />
              ))}
              {/* Handle de resize direito */}
              <Rect
                x={node.width - 8}
                y={7}
                width={14}
                height={node.height - 14}
                fill={node.isResizing ? "#0B2132" : "#2284a1"}
                opacity={0.56}
                cornerRadius={7}
                draggable={false}
                onMouseDown={() => handleResizeStart(idx)}
                style={{ cursor: "ew-resize" }}
              />
            </Group>
          ))}
        </Layer>
      </Stage>
      <div
        style={{
          position: "absolute",
          top: 8,
          left: SIDEBAR_OFFSET + 60,
          fontWeight: 700,
          fontSize: 22,
          color: "#1976d2",
          letterSpacing: 0.5,
          zIndex: 5,
        }}
      >
        Relacionamentos Konva (Power BI UX)
      </div>
    </div>
  );
}
