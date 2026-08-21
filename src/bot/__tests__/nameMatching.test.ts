import { describe, it, expect } from "vitest";
import { globResolve, globSuggest, hasWildcard } from "../nameMatching.js";

const WOODS = ["oak_log", "spruce_log", "birch_log", "jungle_log", "acacia_log", "dark_oak_log"];

describe("hasWildcard", () => {
  it("detects * and ?", () => {
    expect(hasWildcard("*log*")).toBe(true);
    expect(hasWildcard("oak_lo?")).toBe(true);
    expect(hasWildcard("oak_log")).toBe(false);
  });
});

describe("globResolve", () => {
  it("an exact candidate name wins over wildcard semantics", () => {
    // 'oak_log' IS a candidate, so it resolves to itself — the wildcard chars
    // in a name that exists verbatim are literal.
    expect(globResolve("oak_log", [...WOODS, "stone"]));
  });

  it("expands wildcards against the candidates", () => {
    expect(globResolve("*_log", WOODS)).toEqual([...WOODS].sort());
  });

  it("prefix and infix patterns", () => {
    expect(globResolve("oak_*", [...WOODS, "oak_planks", "stone"])).toEqual(["oak_log", "oak_planks"]);
    expect(globResolve("*planks*", ["oak_log", "oak_planks"])).toEqual(["oak_planks"]);
  });

  it("? matches exactly one character", () => {
    expect(globResolve("oak_lo?", ["oak_log", "oak_logs"])).toEqual(["oak_log"]);
  });

  it("no exact match without wildcards returns empty", () => {
    expect(globResolve("logg", WOODS)).toEqual([]);
  });

  it("is case-insensitive", () => {
    expect(globResolve("OAK_LOG", WOODS)).toEqual(["oak_log"]);
  });

  it("regex metacharacters in the pattern are literal", () => {
    expect(globResolve("a.b*c", ["axbyc", "a.b*c"])).toEqual(["a.b*c"]);
  });
});

describe("globSuggest", () => {
  it("suggests infix matches for typos", () => {
    // Call sites wrap typos: globSuggest(`*${name}*`, candidates)
    expect(globSuggest("*ak_lo*", WOODS)).toEqual(["dark_oak_log", "oak_log"]);
  });

  it("respects the limit", () => {
    expect(globSuggest("*", WOODS, 3)).toHaveLength(3);
  });
});
