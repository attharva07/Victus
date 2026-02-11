import { Navigate, Route, Routes } from 'react-router-dom';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { useAuth } from '../lib/authStore';
import { CameraPage } from '../pages/CameraPage';
import { ChatPage } from '../pages/ChatPage';
import { FilesPage } from '../pages/FilesPage';
import { FinancePage } from '../pages/FinancePage';
import { LoginPage } from '../pages/LoginPage';
import { LogsPage } from '../pages/LogsPage';
import { MemoriesPage } from '../pages/MemoriesPage';
import { SettingsPage } from '../pages/SettingsPage';

const Protected = ({ children }: { children: JSX.Element }) => {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return children;
};

export const AppRoutes = () => (
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route
      path="/app"
      element={
        <Protected>
          <DashboardLayout />
        </Protected>
      }
    >
      <Route path="chat" element={<ChatPage />} />
      <Route path="memories" element={<MemoriesPage />} />
      <Route path="finance" element={<FinancePage />} />
      <Route path="files" element={<FilesPage />} />
      <Route path="camera" element={<CameraPage />} />
      <Route path="logs" element={<LogsPage />} />
      <Route path="settings" element={<SettingsPage />} />
      <Route index element={<Navigate to="chat" replace />} />
    </Route>
    <Route path="*" element={<Navigate to="/app/chat" replace />} />
  </Routes>
);
