/**
 * Glob-style name matching for block/item names.
 *
 * Registry names are snake_case, so `*` and `?` cover every practical need
 * without regex escaping foot-guns. Precedence rule (keeps exact names
 * backwards-compatible forever): an exact candidate match always wins, even
 * if the pattern contains wildcards.
 */

export function hasWildcard(pattern: string): boolean {
  return pattern.includes("*") || pattern.includes("?");
}

export function globToRegExp(pattern: string): RegExp {
  const escaped = pattern.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*").replace(/\?/g, ".");
  return new RegExp(`^${escaped}$`, "i");
}

/**
 * Resolve a name/pattern against concrete candidates (inventory contents,
 * container contents, registry keys). Returns the exact match if present,
 * otherwise every candidate matching the glob.
 */
export function globResolve(pattern: string, candidates: Iterable<string>): string[] {
  const list = [...candidates];
  const exact = list.find((name) => name.toLowerCase() === pattern.toLowerCase());
  if (exact !== undefined) return [exact];
  if (!hasWildcard(pattern)) return [];
  const regex = globToRegExp(pattern);
  return list.filter((name) => regex.test(name)).sort();
}

/** Up to `limit` registry names matching the pattern, for error suggestions. */
export function globSuggest(pattern: string, candidates: Iterable<string>, limit = 20): string[] {
  const list = [...candidates];
  const exact = list.find((name) => name.toLowerCase() === pattern.toLowerCase());
  if (exact !== undefined) return [exact];
  const regex = globToRegExp(pattern);
  const matches = list.filter((name) => regex.test(name)).sort();
  if (matches.length > 0) return matches.slice(0, limit);
  return [];
}

export function isGlobAmbiguous(matches: string[]): boolean {
  return matches.length > 1;
}

export function describeMatches(matches: Array<{ name: string; count?: number }>): string {
  return matches.map((m) => (typeof m.count === "number" ? `${m.name} x${m.count}` : m.name)).join(", ");
}
