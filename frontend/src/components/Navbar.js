import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function Navbar({ onLogout, showBack, backTo }) {
  const navigate = useNavigate();
  return (
    <nav className="navbar">
      {showBack && <button onClick={() => navigate(backTo || "/dashboard")}>Voltar</button>}
      <button onClick={onLogout} style={{marginLeft: "auto"}}>Sair</button>
    </nav>
  );
}
