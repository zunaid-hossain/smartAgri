import { NavLink, Outlet } from "react-router-dom";
import { Activity, Bot, ChartNoAxesCombined, Gauge } from "lucide-react";

const nav = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/analytics", label: "Analytics", icon: ChartNoAxesCombined },
  { to: "/ai", label: "AI Assistant", icon: Bot },
  { to: "/status", label: "System Status", icon: Activity },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-[#f5f7f1] text-slate-900">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block">
        <div className="px-6 py-6">
          <p className="text-xl font-bold text-field">SmartAgri AI</p>
          <p className="mt-1 text-sm text-slate-500">Monitoring and auto irrigation</p>
        </div>
        <nav className="space-y-1 px-3">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-3 text-sm font-medium ${
                  isActive ? "bg-field text-white" : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur lg:hidden">
          <div className="flex gap-2 overflow-x-auto">
            {nav.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex shrink-0 items-center gap-2 rounded-md px-3 py-2 text-xs font-semibold ${
                    isActive ? "bg-field text-white" : "bg-slate-100 text-slate-700"
                  }`
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
