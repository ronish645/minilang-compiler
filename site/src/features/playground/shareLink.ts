// Programs travel in the URL as ?code=<base64url(UTF-8 source)>, so a link
// is the whole program: no server, no database.

/** Keep links well under common URL length limits. */
export const MAX_SHARE_BYTES = 6000;

export function encodeSource(source: string): string {
  const bytes = new TextEncoder().encode(source);
  let binary = "";
  bytes.forEach((b) => (binary += String.fromCharCode(b)));
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** Returns null for anything that isn't valid base64url-encoded UTF-8. */
export function decodeSource(encoded: string): string | null {
  try {
    const base64 = encoded.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    return null;
  }
}
