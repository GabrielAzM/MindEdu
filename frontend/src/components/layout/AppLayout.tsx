import { Link, Outlet } from "react-router-dom";
import { motion } from "framer-motion";

import { useAuthStore } from "../../store/authStore";

const navItems = [
  ["/home", "Home"],
  ["/trails", "Trilhas"],
  ["/checkin", "Check-in"],
  ["/coop", "Coop"],
  ["/mascot", "Mascote"],
  ["/profile", "Perfil"],
] as const;

export function AppLayout() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,#c8e0ff_0%,#d1f5e8_45%,#f5fbff_100%)]">
      <header className="sticky top-0 z-20 border-b border-sky-100 bg-white/92 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/home" className="font-heading text-xl font-bold text-ink">
            MindEdu
          </Link>
          <nav className="flex flex-wrap items-center gap-3 text-sm">
            {navItems.map(([to, label]) => (
              <Link key={to} to={to} className="rounded-md px-2 py-1 hover:bg-sky-100">
                {label}
              </Link>
            ))}
            {user?.role === "admin" ? (
              <>
                <Link to="/admin" className="rounded-md bg-ink px-2 py-1 text-white">
                  Admin
                </Link>
                <Link to="/admin/moderation" className="rounded-md border border-sky-300 px-2 py-1 hover:bg-sky-50">
                  Aprovar
                </Link>
              </>
            ) : null}
            <button
              onClick={logout}
              className="rounded-md border border-sky-300 px-2 py-1 hover:bg-sky-50"
              type="button"
            >
              Sair
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  );
}
