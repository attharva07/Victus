import { Camera, Cog, FileText, Landmark, Logs, MessageSquare, BrainCircuit } from 'lucide-react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../lib/authStore';
import { Button } from '../ui/button';

const navItems = [
  { to: '/app/chat', label: 'Chat / Orchestrate', icon: MessageSquare },
  { to: '/app/memories', label: 'Memories', icon: BrainCircuit },
  { to: '/app/finance', label: 'Finance', icon: Landmark },
  { to: '/app/files', label: 'Files', icon: FileText },
  { to: '/app/camera', label: 'Camera', icon: Camera },
  { to: '/app/logs', label: 'Live Logs / Audit Viewer', icon: Logs },
  { to: '/app/settings', label: 'Settings', icon: Cog },
];

export const DashboardLayout = () => {
  const location = useLocation();
  const { setToken, apiBaseUrl } = useAuth();

  return (
    <div className="grid min-h-screen grid-cols-[260px_1fr]">
      <aside className="border-r border-border bg-white p-4">
        <div className="mb-8 text-lg font-semibold">Victus Dashboard</div>
        <nav className="space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to;
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${active ? 'bg-slate-100 font-medium text-slate-900' : 'text-slate-600 hover:bg-slate-50'}`}
              >
                <Icon size={16} />
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div>
        <header className="flex items-center justify-between border-b border-border bg-white px-6 py-4">
          <div>
            <p className="text-sm text-slate-500">Connected API base</p>
            <p className="text-sm font-medium">{apiBaseUrl}</p>
          </div>
          <Button onClick={() => setToken(null)}>Logout</Button>
        </header>
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
