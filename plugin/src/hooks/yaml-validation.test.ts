import { describe, expect, it } from "bun:test";

import { buildValidationMessage, extractYamlPath, isYamlPath } from "./yaml-validation.ts";

describe("yaml validation helpers", () => {
  it("detects yaml paths", () => {
    expect(isYamlPath("table.yaml")).toBe(true);
    expect(isYamlPath("table.yml")).toBe(true);
    expect(isYamlPath("table.json")).toBe(false);
  });

  it("extracts yaml paths from nested tool args", () => {
    expect(extractYamlPath({ filePath: "configs/example.yaml" })).toBe("configs/example.yaml");
    expect(extractYamlPath({ nested: { path: "tables/example.yml" } })).toBe("tables/example.yml");
    expect(extractYamlPath({ path: "notes.md" })).toBeNull();
  });

  it("builds an error message for invalid output", () => {
    const message = buildValidationMessage('{"error":"bad schema"}');
    expect(message).toContain("TABLASSIST VALIDATION ERRORS");
    expect(message).toContain("bad schema");
  });

  it("builds a success message for clean output", () => {
    const message = buildValidationMessage('[{"status":"ok"}]');
    expect(message).toContain("TABLASSIST VALIDATION: PASSED");
  });
});
