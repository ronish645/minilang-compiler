import { useMemo } from "react";
import { cn } from "../../../lib/cn";
import { TOKEN_CLASS, tokenizeLine } from "./highlight";

interface MiniLangCodeProps {
  code: string;
  lineNumbers?: boolean;
  className?: string;
  label?: string; // accessible name for the code region
}

/** Read-only, highlighted MiniLang source. Colors come from theme tokens. */
export function MiniLangCode({ code, lineNumbers = false, className, label }: MiniLangCodeProps) {
  const lines = useMemo(() => code.replace(/\n$/, "").split("\n").map(tokenizeLine), [code]);
  const gutterWidth = `${String(lines.length).length + 1}ch`;

  return (
    <pre
      aria-label={label}
      tabIndex={0}
      className={cn("overflow-x-auto font-mono text-[13px] leading-6 [font-variant-ligatures:none]", className)}
    >
      <code className="block min-w-max">
        {lines.map((tokens, index) => (
          <span key={index} className="flex">
            {lineNumbers && (
              <span
                aria-hidden
                className="mr-4 shrink-0 select-none text-right text-muted/70"
                style={{ width: gutterWidth }}
              >
                {index + 1}
              </span>
            )}
            <span className="whitespace-pre">
              {tokens.length === 0
                ? " "
                : tokens.map((token, i) => (
                    <span key={i} className={TOKEN_CLASS[token.kind]}>
                      {token.text}
                    </span>
                  ))}
            </span>
          </span>
        ))}
      </code>
    </pre>
  );
}
