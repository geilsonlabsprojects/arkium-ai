import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Models from "./pages/Models";
import ApiKeys from "./pages/ApiKeys";
import Playground from "./pages/Playground";
import History from "./pages/History";
import Logs from "./pages/Logs";
import Monitoring from "./pages/Monitoring";
import Users from "./pages/Users";
import SettingsPage from "./pages/Settings";
import Docs from "./pages/Docs";
import Profile from "./pages/Profile";

/** Tabela de rotas da aplicacao. Tudo dentro de ProtectedRoute exige login. */
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/models" element={<Models />} />
        <Route path="/keys" element={<ApiKeys />} />
        <Route path="/playground" element={<Playground />} />
        <Route path="/history" element={<History />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/monitoring" element={<Monitoring />} />
        <Route path="/users" element={<Users />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/docs" element={<Docs />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
