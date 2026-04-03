import { describe, expect, it } from "bun:test";

import { formatSystemPromptResources } from "./system-prompt.ts";

describe("formatSystemPromptResources", () => {
  it("formats all cached resources with headers", () => {
    const parts = formatSystemPromptResources({
      sectionSchema: "schema",
      docsTableConfig: "table docs",
      docsAdvancedExamples: "advanced",
      docsTutorial: "tutorial",
      exampleNoSections: "no sections",
      exampleWithSections: "with sections",
    });

    expect(parts).toHaveLength(6);
    expect(parts[0]).toContain("## Tablassert Section JSON Schema");
    expect(parts[3]).toContain("## Tutorial Reference");
    expect(parts[5]).toContain("with sections");
  });
});
