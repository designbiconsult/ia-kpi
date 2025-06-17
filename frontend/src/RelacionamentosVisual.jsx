import React, { useRef, useEffect, useState } from "react";
import ReactFlow, {
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  NodeResizer,
  Handle,
  Position
} from "reactflow";
import "reactflow/dist/style.css";

function TableNode({ data, selected }) {
  return (
    <div
      style={{
        background: "#fff",
        border: "2.5px solid #2284a1",
        borderRadius: 12,
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
          >
            <Handle
              type="source"
              id={`${data.label}.${col}`}
              position={Position.Right}
              style={{
                background: "rgba(0,0,0,0)",
                width: 12,
                height: 12,
                top: "50%",
                right: -6,
                transform: "translateY(-50%)",
              }}
            />
            <Handle
              type="target"
              id={`${data.label}.${col}`}
              position={Position.Left}
              style={{
                background: "rgba(0,0,0,0)",
                width: 12,
                height: 12,
                top: "50%",
                left: -6,
                transform: "translateY(-50%)",
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

// Defina um canvas GRANDE para poder rolar, mas limite o arrasto dos nodes
function RelacionamentosBI() {
  const [nodes, setNodes, onNodesChange] = useNodesState([
    {
      id: "Pedidos",
      type: "table",
      data: { label: "Pedidos", columns: ["ID", "Data", "ID_Cliente", "Valor", "Status"] },
      position: { x: 100, y: 80 },
      style: { minWidth: 120, minHeight: 36 },
      resizable: true
    },
    {
      id: "Clientes",
      type: "table",
      data: { label: "Clientes", columns: ["ID", "Nome", "Cidade", "UF"] },
      position: { x: 400, y: 150 },
      style: { minWidth: 120, minHeight: 36 },
      resizable: true
    }
  ]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Limite do canvas (igual Power BI)
  const dragBounds = {
    left: 0,
    top: 0,
    right: 1400,
    bottom: 800
  };

  return (
    <div
      style={{
        width: "100vw",
        height: "90vh",
        background: "#f8fafd",
        overflow: "auto", // <- Scroll igual Power BI
        position: "relative"
      }}
    >
      <div style={{ width: 1400, height: 800, position: "relative" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          nodeDragBounds={dragBounds}
          panOnDrag={false} // <- Desabilita o PAN (não arrasta fundo)
          nodesDraggable
          nodesConnectable
        />
      </div>
    </div>
  );
}

export default function AppRelacionamentosBI() {
  return (
    <ReactFlowProvider>
      <RelacionamentosBI />
    </ReactFlowProvider>
  );
}
