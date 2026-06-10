export default function StatusCard({ title, value, detail, icon: Icon, tone = "field" }) {
  const tones = {
    field: "bg-field",
    water: "bg-water",
    earth: "bg-earth",
    warning: "bg-warning",
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
          {detail && <p className="mt-2 text-sm text-slate-500">{detail}</p>}
        </div>
        {Icon && (
          <div className={`rounded-md ${tones[tone]} p-3 text-white`}>
            <Icon size={20} />
          </div>
        )}
      </div>
    </section>
  );
}
