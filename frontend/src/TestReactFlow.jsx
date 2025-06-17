import React, { useRef, useEffect, useState } from "react";
import ReactFlow, { ReactFlowProvider, useNodesState } from "reactflow";
import "reactflow/dist/style.css";

const initialNodes = [
  {
    id: "1",
    position: { x: 80, y: 80 },
    data: { label: "Tabela 1" },
    type: "default"
  },
  {
    id: "2",
    position: { x: 350, y: 80 },
    data: { label: "Tabela 2" },
    type: "default"
  }
];

function TestCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const containerRef = useRef();
  const [dragBounds, setDragBounds] = useState({
    left: 0,
    top: 0,
    right: 0,
    bottom: 0
  });

  useEffect(() => {
    function updateBounds() {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDragBounds({
          left: 0,
          top: 0,
          right: rect.width,
          bottom: rect.height
        });
      }
    }
    updateBounds();
    window.addEventListener("resize", updateBounds);
    return () => window.removeEventListener("resize", updateBounds);
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100vw",
        height: "90vh",
        background: "#f8fafd",
        position: "relative",
        overflow: "hidden"
      }}
    >
      <ReactFlow
        nodes={nodes}
        onNodesChange={onNodesChange}
        nodeDragBounds={dragBounds}
        fitView
        minZoom={0.3}
        maxZoom={1.5}
        panOnDrag
        nodesDraggable
      />
    </div>
  );
}

export default function TestReactFlow() {
  return (
    <ReactFlowProvider>
      <TestCanvas />
    </ReactFlowProvider>
  );
}
