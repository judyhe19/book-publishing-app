export function Card({ children }) {
  return <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">{children}</div>;
}

export function CardHeader({ title, subtitle }) {
  return (
    <div className="p-6 border-b border-slate-100">
      <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-slate-600">{subtitle}</p>}
    </div>
  );
}

export function CardContent({ children }) {
  return <div className="p-6">{children}</div>;
}