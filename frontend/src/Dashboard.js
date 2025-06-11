import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import SetorTabs from "./components/SetorTabs";
import IndicadorCard from "./components/IndicadorCard";
import { api } from ".\api";

const setores = ["Financeiro", "Comercial", "Produção"];

export default function Dashboard({ user, onLogout }) {
  const [setor, setSetor] = useState("Financeiro");
  const [indicadores, setIndicadores] = useState([]);
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchIndicadores() {
      try {
        const { data } = await api.get(`/indicadores?setor=${setor}`);
        setIndicadores(data);
      } catch {
        setIndicadores([]);
        setMsg("Não foi possível carregar indicadores.");
      }
    }
    fetchIndicadores();
  }, [setor]);

  return (
    <div className="container">
      <Navbar onLogout={onLogout} />
      <h2>Dashboard de Indicadores</h2>
      <SetorTabs setores={setores} setor={setor} setSetor={setSetor} />
      <div style={{ display: "flex", gap: 16, margin: "32px 0" }}>
        {indicadores.length ? (
          indicadores.map((i, idx) => (
            <IndicadorCard key={idx} titulo={i.titulo} valor={i.valor} />
          ))
        ) : (
          <div>Nenhum indicador encontrado.</div>
        )}
      </div>
      <button onClick={() => navigate("/conexao")}>Configurar conexão</button>
      <button onClick={() => navigate("/sincronizar")}>Sincronizar tabelas/views</button>
    </div>
  );
}
