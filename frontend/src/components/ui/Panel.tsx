import type { PropsWithChildren, ReactNode } from "react";

interface PanelProps extends PropsWithChildren {
  title: string;
  className?: string;
  action?: ReactNode;
  titleId?: string;
}

export function Panel({ title, className = "", action, children, titleId }: PanelProps) {
  const headingId = titleId ?? `${className || "panel"}-title`;

  return (
    <section className={`panel ${className}`} aria-labelledby={headingId}>
      <div className="panel__header">
        <h2 id={headingId}>{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}
