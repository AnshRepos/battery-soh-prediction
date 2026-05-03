import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useState } from 'react'

// ─── Nav items ────────────────────────────────────────────────────────────────
const NAV = [
  {
    to: '/',
    exact: true,
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
    label: 'Dashboard',
  },
  {
    to: '/leaderboard',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.492a46.32 46.32 0 012.916.52 6.003 6.003 0 01-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0" />
      </svg>
    ),
    label: 'Leaderboard',
  },
  {
    to: '/plots',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
      </svg>
    ),
    label: 'Plots',
  },
  {
    to: '/about',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
      </svg>
    ),
    label: 'About',
  },
]

// ─── Sidebar link ─────────────────────────────────────────────────────────────
function SideLink({ item }) {
  return (
    <NavLink
      to={item.to}
      end={item.exact}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
          isActive
            ? 'bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20'
            : 'text-text-secondary hover:text-text-primary hover:bg-surface-2'
        }`
      }
    >
      {item.icon}
      <span className="font-sans font-medium">{item.label}</span>
    </NavLink>
  )
}

// ─── Layout ───────────────────────────────────────────────────────────────────
export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  // close drawer on route change
  // eslint-disable-next-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen flex bg-surface">
      {/* ── Desktop Sidebar ── */}
      <aside className="hidden lg:flex flex-col w-60 shrink-0 border-r border-surface-border bg-surface-1 fixed inset-y-0 left-0 z-30">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-surface-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent-cyan/10 border border-accent-cyan/30 flex items-center justify-center">
              <svg className="w-4 h-4 text-accent-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 10.5h.375c.621 0 1.125.504 1.125 1.125v2.25c0 .621-.504 1.125-1.125 1.125H21M4.5 10.5H18V15H4.5v-4.5zM3.75 18h15A2.25 2.25 0 0021 15.75v-1.5a2.25 2.25 0 00-2.25-2.25H3.75A2.25 2.25 0 001.5 14.25v1.5A2.25 2.25 0 003.75 18z" />
              </svg>
            </div>
            <div>
              <p className="font-display font-semibold text-sm text-text-primary leading-tight">Battery SOH</p>
              <p className="font-mono text-[10px] text-text-muted leading-tight">Activation Lab</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          <p className="section-title px-3 mb-3">Navigation</p>
          {NAV.map((item) => (
            <SideLink key={item.to} item={item} />
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-surface-border">
          <div className="bg-surface-2 rounded-lg p-3">
            <p className="font-mono text-[10px] text-text-muted mb-1">Dataset</p>
            <p className="text-xs text-text-secondary">NASA Li-ion Aging</p>
            <p className="font-mono text-[10px] text-accent-cyan mt-1">B0005 · B0006 · B0007 · B0018</p>
          </div>
        </div>
      </aside>

      {/* ── Mobile Header ── */}
      <header className="lg:hidden fixed top-0 inset-x-0 z-40 bg-surface-1 border-b border-surface-border flex items-center justify-between px-4 h-14">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-accent-cyan/10 border border-accent-cyan/30 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-accent-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 10.5h.375c.621 0 1.125.504 1.125 1.125v2.25c0 .621-.504 1.125-1.125 1.125H21M4.5 10.5H18V15H4.5v-4.5z" />
            </svg>
          </div>
          <span className="font-display font-semibold text-sm">Battery SOH</span>
        </div>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 rounded-lg hover:bg-surface-2 text-text-secondary"
          aria-label="Toggle menu"
        >
          {mobileOpen ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          )}
        </button>
      </header>

      {/* ── Mobile Drawer ── */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-30 bg-black/60" onClick={() => setMobileOpen(false)}>
          <aside
            className="absolute left-0 top-14 bottom-0 w-60 bg-surface-1 border-r border-surface-border"
            onClick={(e) => e.stopPropagation()}
          >
            <nav className="px-3 py-4 space-y-1">
              {NAV.map((item) => (
                <div key={item.to} onClick={() => setMobileOpen(false)}>
                  <SideLink item={item} />
                </div>
              ))}
            </nav>
          </aside>
        </div>
      )}

      {/* ── Main content ── */}
      <main className="flex-1 lg:ml-60 pt-14 lg:pt-0 min-h-screen">
        <div className="p-5 lg:p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
