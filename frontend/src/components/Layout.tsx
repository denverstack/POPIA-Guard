import { Link, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { ShieldCheck, LogOut } from "lucide-react";
import { useAuth } from "@/lib/use-auth";

export function Layout({ children }: { children: ReactNode }) {
  const { logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
          <Link to="/dashboard" className="flex items-center gap-2 text-text-primary">
            <ShieldCheck className="h-5 w-5 text-accent" aria-hidden="true" />
            <span className="text-sm font-semibold tracking-tight">POPIA Guard</span>
          </Link>
          {isAuthenticated && (
            <button
              type="button"
              onClick={handleLogout}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              Log out
            </button>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
    </div>
  );
}
