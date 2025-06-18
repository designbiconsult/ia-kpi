import React, { useRef, useState } from "react";
import { Stage, Layer, Rect, Group, Text } from "react-konva";

// Parâmetros do canvas
const CANVAS_W = 1700; // Largura total do canvas
const CANVAS_H = 900;  // Altura total do canvas
const SIDEBAR_OFFSET = 0; // Ajuste se tiver menu lateral fixo (ex: 60)
const MIN_WIDTH = 140;
const MAX_WIDTH = 430;
const MIN_HEIGHT = 45;

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
  const dragOffset = useRef({ x: 0, y: 0 });

  // Handler de arrasto (NÃO deixa passar do limite!)
  const handleDragMove = (idx, e) => {
    let x = e.target.x();
    let y = e.target.y();
    // Limite ESQUERDA (SIDEBAR), DIREITA, TOPO, BASE
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

  // Drag Start/End (visual feedback)
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

  // Resize só pelo lado direito
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
    // X do mouse relativo ao node
    let nextWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, e.evt.layerX - n.x));
    // Limite na direita
    if (n.x + nextWidth > CANVAS_W) nextWidth = CANVAS_W - n.x - 2;
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

  return (
    <div
      style={{
        width: CANVAS_W + "px",
        background: "#e4f3fa",
        borderRadius: 24,
        boxShadow: "0 6px 38px #1976d218",
        border: "6px solid #1976d2",
        position: "relative",
        marginLeft: 0, // AGORA NUNCA centraliza!
      }}
    >
      <Stage width={CANVAS_W} height={CANVAS_H}
        style={{ borderRadius: 18, background: "#f8fafd" }}
        onMouseMove={handleResizeMove}
        onMouseUp={handleResizeEnd}
      >
        {/* Delimitação visual do espaço */}
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
          left: 16,
          fontWeight: 700,
          fontSize: 22,
          color: "#1976d2",
          letterSpacing: 0.5
        }}
      >
        Relacionamentos 
      </div>
    </div>
  );
}
