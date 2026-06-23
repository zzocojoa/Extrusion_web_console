import type { ReactNode } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Copy, RotateCcw } from "lucide-react";

export interface DataTableColumn<Row> {
  id: string;
  header: ReactNode;
  width: number;
  minWidth?: number;
  maxWidth?: number;
  className?: string;
  headerClassName?: string;
  render: (row: Row) => ReactNode;
}

interface ResizableDataTableProps<Row> {
  columns: Array<DataTableColumn<Row>>;
  rows: Row[];
  getRowKey: (row: Row) => string | number;
  storageKey: string;
  className?: string;
  empty?: ReactNode;
  resetLabel: string;
  tableLabel?: string;
  rowClassName?: (row: Row) => string | undefined;
}

interface DragState {
  columnId: string;
  startX: number;
  startWidth: number;
  minWidth: number;
  maxWidth: number;
}

export function ResizableDataTable<Row>({
  columns,
  rows,
  getRowKey,
  storageKey,
  className,
  empty,
  resetLabel,
  tableLabel,
  rowClassName,
}: ResizableDataTableProps<Row>) {
  const dragState = useRef<DragState | null>(null);
  const [storedWidths, setStoredWidths] = useState<Record<string, number>>(() => readStoredWidths(storageKey));

  useEffect(() => {
    const keys = new Set(columns.map((column) => column.id));
    const nextWidths = Object.fromEntries(
      Object.entries(storedWidths).filter(([key, value]) => keys.has(key) && Number.isFinite(value)),
    );
    if (Object.keys(nextWidths).length !== Object.keys(storedWidths).length) {
      setStoredWidths(nextWidths);
    }
  }, [columns, storedWidths]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(storageKey, JSON.stringify(storedWidths));
  }, [storageKey, storedWidths]);

  useEffect(() => {
    function handlePointerMove(event: PointerEvent) {
      const active = dragState.current;
      if (!active) return;
      const width = clamp(active.startWidth + event.clientX - active.startX, active.minWidth, active.maxWidth);
      setStoredWidths((current) => ({ ...current, [active.columnId]: width }));
    }

    function handlePointerUp() {
      dragState.current = null;
      document.body.classList.remove("is-resizing-column");
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);
      document.body.classList.remove("is-resizing-column");
    };
  }, []);

  const effectiveColumns = useMemo(
    () =>
      columns.map((column) => {
        const minWidth = column.minWidth ?? 72;
        const maxWidth = column.maxWidth ?? 720;
        return {
          ...column,
          minWidth,
          maxWidth,
          effectiveWidth: clamp(storedWidths[column.id] ?? column.width, minWidth, maxWidth),
        };
      }),
    [columns, storedWidths],
  );

  const tableMinWidth = effectiveColumns.reduce((total, column) => total + column.effectiveWidth, 0);

  function startResize(column: (typeof effectiveColumns)[number], event: React.PointerEvent<HTMLElement>) {
    event.preventDefault();
    event.stopPropagation();
    dragState.current = {
      columnId: column.id,
      startX: event.clientX,
      startWidth: column.effectiveWidth,
      minWidth: column.minWidth,
      maxWidth: column.maxWidth,
    };
    document.body.classList.add("is-resizing-column");
  }

  function resizeFromHeaderEdge(column: (typeof effectiveColumns)[number], event: React.PointerEvent<HTMLTableCellElement>) {
    if (event.button !== 0) return;
    const rect = event.currentTarget.getBoundingClientRect();
    if (rect.right - event.clientX > 12) return;
    startResize(column, event);
  }

  function resizeByKeyboard(column: (typeof effectiveColumns)[number], event: React.KeyboardEvent<HTMLButtonElement>) {
    const direction = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (!direction) return;
    event.preventDefault();
    setStoredWidths((current) => ({
      ...current,
      [column.id]: clamp(column.effectiveWidth + direction * 16, column.minWidth, column.maxWidth),
    }));
  }

  function resetWidths() {
    setStoredWidths({});
  }

  if (rows.length === 0) return <>{empty}</>;

  return (
    <div className="resizable-table">
      <div className="resizable-table__actions">
        <button className="button button--secondary button--compact" type="button" onClick={resetWidths}>
          <RotateCcw size={14} aria-hidden="true" />
          {resetLabel}
        </button>
      </div>
      <div className="table-scroll table-scroll--resizable">
        <table
          aria-label={tableLabel}
          className={`data-table data-table--resizable ${className ?? ""}`.trim()}
          style={{ minWidth: tableMinWidth }}
        >
          <colgroup>
            {effectiveColumns.map((column) => (
              <col key={column.id} style={{ width: column.effectiveWidth }} />
            ))}
          </colgroup>
          <thead>
            <tr>
              {effectiveColumns.map((column) => (
                <th className={column.headerClassName} key={column.id} scope="col" onPointerDown={(event) => resizeFromHeaderEdge(column, event)}>
                  <span className="resizable-table__header-content">{column.header}</span>
                  <button
                    aria-label={`Resize ${column.id}`}
                    className="resizable-table__resize-handle"
                    type="button"
                    onKeyDown={(event) => resizeByKeyboard(column, event)}
                    onPointerDown={(event) => startResize(column, event)}
                  />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr className={rowClassName?.(row)} key={getRowKey(row)}>
                {effectiveColumns.map((column) => (
                  <td className={column.className} key={column.id}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

interface DetailCellProps {
  value: string | null | undefined;
  preview?: ReactNode;
  className?: string;
  copyLabel: string;
  closeLabel: string;
  detailLabel: string;
  allowCopy?: boolean;
  lines?: 1 | 2 | 3;
  monospace?: boolean;
}

export function DetailCell({
  value,
  preview,
  className,
  copyLabel,
  closeLabel,
  detailLabel,
  allowCopy = false,
  lines = 1,
  monospace = false,
}: DetailCellProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLSpanElement>(null);
  const text = value?.trim() || "-";

  useEffect(() => {
    if (!open) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    function closeOnOutsidePointerDown(event: PointerEvent) {
      const root = rootRef.current;
      if (!root || !(event.target instanceof Node)) return;
      if (!root.contains(event.target)) setOpen(false);
    }
    window.addEventListener("keydown", closeOnEscape);
    document.addEventListener("pointerdown", closeOnOutsidePointerDown);
    return () => {
      window.removeEventListener("keydown", closeOnEscape);
      document.removeEventListener("pointerdown", closeOnOutsidePointerDown);
    };
  }, [open]);

  async function copyValue() {
    if (!allowCopy || text === "-" || typeof navigator === "undefined" || !navigator.clipboard) return;
    await navigator.clipboard.writeText(text).catch(() => undefined);
  }

  return (
    <span ref={rootRef} className={`detail-cell detail-cell--lines-${lines} ${monospace ? "detail-cell--mono" : ""} ${className ?? ""}`.trim()}>
      <button className="detail-cell__trigger" title={text} type="button" onClick={() => setOpen(true)}>
        {preview ?? text}
      </button>
      {open ? (
        <span className="detail-popover" role="dialog" aria-label={detailLabel}>
          <span className="detail-popover__header">
            <strong>{detailLabel}</strong>
            <span className="detail-popover__actions">
              {allowCopy ? (
                <button className="button button--secondary button--compact" type="button" onClick={copyValue}>
                  <Copy size={14} aria-hidden="true" />
                  {copyLabel}
                </button>
              ) : null}
              <button className="button button--secondary button--compact" type="button" onClick={() => setOpen(false)}>
                {closeLabel}
              </button>
            </span>
          </span>
          <span className="detail-popover__body">{text}</span>
        </span>
      ) : null}
    </span>
  );
}

export interface TablePaginationLabels {
  range: (start: number, end: number, total: number) => string;
  pageSize: string;
  first: string;
  previous: string;
  next: string;
  last: string;
  page: (current: number, total: number) => string;
}

interface TablePaginationProps {
  pageIndex: number;
  pageSize: number;
  totalItems: number;
  pageSizeOptions: number[];
  labels: TablePaginationLabels;
  onPageIndexChange: (pageIndex: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

export function TablePagination({
  pageIndex,
  pageSize,
  totalItems,
  pageSizeOptions,
  labels,
  onPageIndexChange,
  onPageSizeChange,
}: TablePaginationProps) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePageIndex = clamp(pageIndex, 0, totalPages - 1);
  const start = totalItems === 0 ? 0 : safePageIndex * pageSize + 1;
  const end = Math.min(totalItems, (safePageIndex + 1) * pageSize);
  const pages = compactPageList(safePageIndex, totalPages);

  function changePage(nextPageIndex: number) {
    onPageIndexChange(clamp(nextPageIndex, 0, totalPages - 1));
  }

  return (
    <div className="table-pagination">
      <span className="table-pagination__range">{labels.range(start, end, totalItems)}</span>
      <label>
        {labels.pageSize}
        <select value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
          {pageSizeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <div className="table-pagination__buttons" aria-label={labels.page(safePageIndex + 1, totalPages)}>
        <button aria-label={labels.first} className="button button--secondary button--compact" type="button" disabled={safePageIndex === 0} onClick={() => changePage(0)}>
          &lt;&lt;
        </button>
        <button aria-label={labels.previous} className="button button--secondary button--compact" type="button" disabled={safePageIndex === 0} onClick={() => changePage(safePageIndex - 1)}>
          &lt;
        </button>
        <span className="table-pagination__compact-page">{labels.page(safePageIndex + 1, totalPages)}</span>
        <span className="table-pagination__number-list">
          {pages.map((page, index) =>
            page === "ellipsis" ? (
              <span aria-hidden="true" className="table-pagination__ellipsis" key={`ellipsis-${index}`}>
                ...
              </span>
            ) : (
              <button
                aria-current={page === safePageIndex ? "page" : undefined}
                className="button button--secondary button--compact"
                key={page}
                type="button"
                onClick={() => changePage(page)}
              >
                {page + 1}
              </button>
            ),
          )}
        </span>
        <button aria-label={labels.next} className="button button--secondary button--compact" type="button" disabled={safePageIndex >= totalPages - 1} onClick={() => changePage(safePageIndex + 1)}>
          &gt;
        </button>
        <button aria-label={labels.last} className="button button--secondary button--compact" type="button" disabled={safePageIndex >= totalPages - 1} onClick={() => changePage(totalPages - 1)}>
          &gt;&gt;
        </button>
      </div>
    </div>
  );
}

export function readStoredPageSize(storageKey: string, defaultValue: number, allowed: number[]) {
  if (typeof window === "undefined") return defaultValue;
  const stored = Number(window.localStorage.getItem(storageKey));
  return allowed.includes(stored) ? stored : defaultValue;
}

function readStoredWidths(storageKey: string): Record<string, number> {
  if (typeof window === "undefined") return {};
  try {
    const parsed = JSON.parse(window.localStorage.getItem(storageKey) ?? "{}");
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    return Object.fromEntries(
      Object.entries(parsed)
        .filter(([, value]) => typeof value === "number" && Number.isFinite(value))
        .map(([key, value]) => [key, value as number]),
    );
  } catch {
    return {};
  }
}

function compactPageList(currentPage: number, totalPages: number): Array<number | "ellipsis"> {
  const pages = new Set([0, totalPages - 1, currentPage - 1, currentPage, currentPage + 1].filter((page) => page >= 0 && page < totalPages));
  const sorted = [...pages].sort((a, b) => a - b);
  const result: Array<number | "ellipsis"> = [];
  for (const page of sorted) {
    const previous = result[result.length - 1];
    if (typeof previous === "number" && page - previous > 1) result.push("ellipsis");
    result.push(page);
  }
  return result;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
