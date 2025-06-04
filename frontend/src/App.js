import React, { useEffect, useState } from "react";
import Diagram from "./Diagram";
import axios from "axios";

function App() {
  const [tabelas, setTabelas] = useState([]);
  const [colunas, setColunas] = useState({});
  const [relacionamentos, setRelacionamentos] = useState([]);

  // Carrega tabelas
  useEffect(() => {
    axios.get("http://localhost:8000/tabelas").then(res => setTabelas(res.data));
  }, []);

  // Carrega colunas de cada tabela
  useEffect(() => {
    tabelas.forEach(tb => {
      if (!colunas[tb]) {
        axios.get(`http://localhost:8000/colunas/${tb}`).then(res => {
          setColunas(cols => ({ ...cols, [tb]: res.data }));
        });
      }
    });
  }, [tabelas]);

  // Carrega relacionamentos já salvos
  useEffect(() => {
    axios.get("http://localhost:8000/relacionamentos").then(res => setRelacionamentos(res.data));
  }, []);

  return (
    <div style={{ height: "100vh", width: "100vw" }}>
      <h2 style={{ textAlign: "center" }}>Relacionamentos de Tabelas (Clique e arraste colunas)</h2>
      <Diagram tabelas={tabelas} colunas={colunas} relacionamentos={relacionamentos} setRelacionamentos={setRelacionamentos} />
    </div>
  );
}

export default App;
