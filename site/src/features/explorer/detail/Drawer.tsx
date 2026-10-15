import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

interface DrawerProps {
  labelledBy: string;
  onClose: () => void;
  children: ReactNode;
}

const FOCUSABLE =
  'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])';

const SLIDE_CSS = `
@keyframes ml-drawer-in { from { transform: translateX(32px); opacity: 0; } }
@keyframes ml-fade-in { from { opacity: 0; } }
`;

/** Keep Tab inside the panel while it is open. */
function trapTab(event: KeyboardEvent, panel: HTMLElement) {
  const items = [...panel.querySelectorAll<HTMLElement>(FOCUSABLE)].filter((el) => el.offsetParent !== null);
  if (items.length === 0) return;
  const first = items[0];
  const last = items[items.length - 1];
  const active = document.activeElement;
  if (event.shiftKey && (active === first || active === panel)) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus();
  }
}

/** The app root. The sheet is portaled outside it, so the whole page behind can go inert. */
function setBackgroundInert(inert: boolean) {
  const root = document.getElementById("root");
  if (root) root.inert = inert;
}

/**
 * A modal side sheet: right-hand panel on desktop, full screen on phones.
 * Moves focus in on open, traps Tab, closes on Esc or backdrop click, and
 * returns focus to whatever opened it. It renders in a portal so the page
 * behind (everything in #root) can be made inert.
 */
export function Drawer({ labelledBy, onClose, children }: DrawerProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    const panel = panelRef.current;
    panel?.focus();

    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onCloseRef.current();
      else if (event.key === "Tab" && panel) trapTab(event, panel);
    };
    document.addEventListener("keydown", onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    setBackgroundInert(true);

    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
      setBackgroundInert(false);
      if (opener && document.contains(opener)) opener.focus();
    };
  }, []);

  return createPortal(
    <div className="fixed inset-0 z-50">
      <style>{SLIDE_CSS}</style>
      <div
        aria-hidden
        onClick={onClose}
        className="absolute inset-0 bg-page/70 backdrop-blur-[2px]"
        style={{ animation: "ml-fade-in 150ms ease-out" }}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        tabIndex={-1}
        className="absolute inset-y-0 right-0 flex w-full flex-col border-l border-border bg-surface shadow-2xl outline-none sm:max-w-2xl"
        style={{ animation: "ml-drawer-in 200ms ease-out" }}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}
