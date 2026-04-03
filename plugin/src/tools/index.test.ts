import { describe, expect, it } from "bun:test";

import { createAllTools } from "./index.ts";

describe("createAllTools", () => {
  it("registers the full expected tool set", () => {
    const tools = createAllTools(async (command, args) => `${command}:${args.join(",")}`);

    expect(Object.keys(tools).sort()).toEqual([
      "docs-category",
      "docs-predicate",
      "docs-qualifier",
      "download-pmc-tar",
      "excel-sheets",
      "extract-text",
      "get-curie-info",
      "list-categories",
      "list-predicates",
      "list-qualifiers",
      "preview-csv",
      "preview-excel",
      "resolve-taxon-id",
      "search-curies",
      "search-gene-curies",
      "section-schema",
      "validate-config-file",
      "validate-config-str",
      "validate-section-str",
    ]);
  });
});
