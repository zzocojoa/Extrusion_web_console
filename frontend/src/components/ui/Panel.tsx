import type { PropsWithChildren, ReactNode } from "react";

interface PanelProps extends PropsWithChildren {
  title: string;
  className?: string;
  action?: ReactNode;
}

export function Panel({ title, className = "", action, children }: PanelProps) {
  return (
    <section className={`panel ${className}`} aria-labelledby={`${title}-title`}>
      <div className="panel__header">
        <h2 id={`${title}-title`}>{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}
