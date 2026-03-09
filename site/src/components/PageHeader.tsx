export function PageHeader({
  title,
  description,
  eyebrow,
}: {
  title: string;
  description: string;
  eyebrow?: string;
}) {
  return (
    <div className="mb-12">
      {eyebrow && (
        <p className="text-sm text-electric font-mono mb-3 uppercase tracking-wider">
          {eyebrow}
        </p>
      )}
      <h1 className="font-heading text-4xl md:text-6xl mb-4">
        <span className="gradient-text">{title}</span>
      </h1>
      <p className="text-xl text-dim max-w-2xl leading-relaxed">{description}</p>
    </div>
  );
}
