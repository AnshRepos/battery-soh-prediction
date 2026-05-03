/**
 * PageHeader.jsx
 * Consistent top section for all pages with title, subtitle, and optional actions.
 */
export default function PageHeader({ eyebrow, title, subtitle, actions }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
      <div>
        {eyebrow && (
          <p className="section-title mb-2">{eyebrow}</p>
        )}
        <h1 className="font-display text-2xl lg:text-3xl font-semibold text-text-primary leading-tight">
          {title}
        </h1>
        {subtitle && (
          <p className="text-sm text-text-secondary mt-1.5 max-w-lg">{subtitle}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  )
}
