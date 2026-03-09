export function Timeline({
  steps,
}: {
  steps: { title: string; description: string }[];
}) {
  return (
    <div className="space-y-0">
      {steps.map((step, i) => (
        <div key={i} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="w-8 h-8 rounded-full bg-electric/10 border border-electric/30 flex items-center justify-center text-sm font-mono text-electric">
              {i + 1}
            </div>
            {i < steps.length - 1 && (
              <div className="w-px flex-1 bg-gs-border my-2" />
            )}
          </div>
          <div className="pb-8">
            <h3 className="font-medium text-text mb-1">{step.title}</h3>
            <p className="text-sm text-dim">{step.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
