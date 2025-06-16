import * as React from 'react';
import { Drawer, List, ListItem, ListItemIcon, ListItemText, IconButton, Toolbar, Divider, Box } from '@mui/material';
import PeopleIcon from '@mui/icons-material/People';
import SettingsIcon from '@mui/icons-material/Settings';
import SyncAltIcon from '@mui/icons-material/SyncAlt';
import TableChartIcon from '@mui/icons-material/TableChart';
import DeviceHubIcon from '@mui/icons-material/DeviceHub';
import DashboardIcon from '@mui/icons-material/Dashboard';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import { useNavigate } from "react-router-dom";


const drawerWidth = 230;

export default function Sidebar({ open, setOpen }) {
  const navigate = useNavigate();

  const menuItems = [
    { label: "Dashboard", icon: <DashboardIcon />, path: "/dashboard" },
    { label: "Cadastro de Usuários", icon: <PeopleIcon />, path: "/admin" },
    { label: "Configuração de Conexão", icon: <SettingsIcon />, path: "/conexao" },
    { label: "Sincronismo de Tabelas", icon: <SyncAltIcon />, path: "/sincronizar" },
    { label: "Relacionamentos", icon: <DeviceHubIcon />, path: "/relacionamentos" },
    { label: "Relacionamentos Visual", icon: <TableChartIcon />, path: "/relacionamentos-visual" },

    // { label: "Visual Relacionamentos", icon: <TableChartIcon />, path: "/relacionamentos-visual" }, // Extra opcional
  ];

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          bgcolor: "#e6f0fa"
        },
      }}
    >
      <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
        <Box fontWeight={700} fontSize={20} color="#0B2132" ml={1}>
          IA-KPI
        </Box>
        <IconButton onClick={() => setOpen(false)}>
          <ChevronLeftIcon />
        </IconButton>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map(item => (
          <ListItem
            button
            key={item.label}
            onClick={() => {
              navigate(item.path);
              setOpen(false);
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}
