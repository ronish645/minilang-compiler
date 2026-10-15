import {
  createContext,
  useContext,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type FocusEvent,
  type PointerEvent,
  type ReactNode,
} from "react";
import { cn } from "../../../lib/cn";

// One tooltip per chart. Marks call tip.bind(content, label) to get pointer and
// focus handlers, so hover and keyboard show the same details. Tooltips only
// enhance: every value is also in the chart's table view.

interface TipState {
  x: number;
  y: number;
  layerWidth: number;
  content: ReactNode;
}

interface TipApi {
  showAt: (clientX: number, clientY: number, content: ReactNode) => void;
  hide: () => void;
}

const TipContext = createContext<TipApi | null>(null);
const EDGE = 4;
const OFFSET = 12;

function TooltipBox({ tip }: { tip: TipState }) {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useLayoutEffect(() => {
    const node = ref.current;
    if (node) setSize({ width: node.offsetWidth, height: node.offsetHeight });
  }, [tip.content]);

  const maxLeft = Math.max(EDGE, tip.layerWidth - size.width - EDGE);
  const left = Math.min(Math.max(tip.x - size.width / 2, EDGE), maxLeft);
  const above = tip.y - size.height - OFFSET;
  const top = above >= -size.height / 2 ? above : tip.y + OFFSET + 8;

  return (
    <div
      ref={ref}
      role="tooltip"
      style={{ left, top, visibility: size.width ? "visible" : "hidden" }}
      className="pointer-events-none absolute z-20 max-w-64 rounded-lg border border-border bg-surface px-3 py-2 text-xs text-ink-2 shadow-lg"
    >
      {tip.content}
    </div>
  );
}

export function TooltipLayer({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [tip, setTip] = useState<TipState | null>(null);

  const api = useMemo<TipApi>(
    () => ({
      showAt: (clientX, clientY, content) => {
        const rect = ref.current?.getBoundingClientRect();
        if (!rect) return;
        setTip({ x: clientX - rect.left, y: clientY - rect.top, layerWidth: rect.width, content });
      },
      hide: () => setTip(null),
    }),
    [],
  );

  return (
    <TipContext.Provider value={api}>
      <div ref={ref} className={cn("relative", className)} onPointerLeave={api.hide}>
        {children}
        {tip && <TooltipBox tip={tip} />}
      </div>
    </TipContext.Provider>
  );
}

export interface TipHandlers {
  tabIndex: number;
  "aria-label": string;
  onPointerMove: (event: PointerEvent<HTMLElement>) => void;
  onPointerLeave: () => void;
  onFocus: (event: FocusEvent<HTMLElement>) => void;
  onBlur: () => void;
}

/** Returns a binder: spread tip.bind(content, label) onto any mark. */
export function useTip() {
  const api = useContext(TipContext);
  return {
    bind: (content: ReactNode, label: string): TipHandlers => ({
      tabIndex: 0,
      "aria-label": label,
      onPointerMove: (event) => api?.showAt(event.clientX, event.clientY, content),
      onPointerLeave: () => api?.hide(),
      onFocus: (event) => {
        const rect = event.currentTarget.getBoundingClientRect();
        api?.showAt(rect.left + rect.width / 2, rect.top, content);
      },
      onBlur: () => api?.hide(),
    }),
  };
}

interface TipBodyProps {
  value: ReactNode;
  label: ReactNode;
  detail?: ReactNode;
  keyColor?: string;
}

/** Tooltip content: the value leads, the label follows, a line key carries identity. */
export function TipBody({ value, label, detail, keyColor }: TipBodyProps) {
  return (
    <div className="flex items-start gap-2">
      {keyColor && (
        <span aria-hidden className="mt-2 h-0.5 w-3 shrink-0 rounded-full" style={{ background: keyColor }} />
      )}
      <div className="min-w-0">
        <div className="text-sm font-semibold tabular-nums text-ink">{value}</div>
        <div className="text-ink-2">{label}</div>
        {detail && <div className="mt-0.5 text-muted">{detail}</div>}
      </div>
    </div>
  );
}
