export default function Card({ hover = false, className = "", children, ...props }) {
  return (
    <div
      className={`rounded-2xl border border-line bg-white shadow-soft
        ${hover ? "transition-all duration-200 ease-out hover:-translate-y-1 hover:shadow-lift hover:border-slate-300" : ""}
        ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
