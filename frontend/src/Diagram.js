import React, { useEffect, useState } from 'react';
import ReactFlow, { Controls, Background } from 'reactflow';
//import 'reactflow/dist/style.css';
import { listarTabelas, listarColunas, listarRelacionamentos, criarRelacionamento, deletarRelacionamento } from '.api';

function Diagram({ user }) {
  const [tabelas, setTabelas] = useState([]);
  const [colunas, setColunas] = useState({});
  const [relacionamentos, setRelacionamentos] = useState([]);

  // Carregar tabelas e relacionamentos ao montar
  useEffect(() => {
    listarTabelas().then(res => setTabelas(res.data));
    listarRelacionamentos().then(res => setRelacionamentos(res.data));
  }, []);

  useEffect(() => {
    // Carregar colunas para cada tabela
    tabelas.forEach(tb => {
      if (!colunas[tb]) {
        listarColunas(tb).then(res =>
          setColunas(c => ({ ...c, [tb]: res.data }))
        );
      }
    });
  }, [tabelas]);

  // Aqui você implementaria a lógica de drag&drop (exemplo básico abaixo)
  return (
    <div className="container">
      <h2>Relacionamentos de Tabelas (Clique e arraste colunas)</h2>
      <ReactFlow nodes={[]} edges={[]} fitView>
        <Controls />
        <Background />
      </ReactFlow>
      {/* Você vai evoluir para montar os nodes/edges de verdade */}
    </div>
  );
}
export default Diagram;
