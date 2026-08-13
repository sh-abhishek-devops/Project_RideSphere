import { Outlet } from "react-router-dom";
import { useState } from "react";

import { Header } from "components/Header";
import { Sidebar } from "components/Sidebar";
import { useAuth } from "hooks/useAuth";

export function AppShell() {
  const { logout, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  if (!user) {
    return null;
  }

  return (
    <div className="app-shell">
      <Sidebar isOpen={isOpen} onNavigate={() => setIsOpen(false)} role={user.role} />
      <div className="app-shell__content">
        <Header onLogout={logout} onMenuToggle={() => setIsOpen((value) => !value)} user={user} />
        <main className="app-shell__main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
