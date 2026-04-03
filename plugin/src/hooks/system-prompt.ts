import type { Hooks } from "@opencode-ai/plugin";

import type { CachedResourceMap, TablassistCache } from "../cache.ts";

export function formatSystemPromptResources(resources: CachedResourceMap): string[] {
  return [
    ["## Tablassert Section JSON Schema", resources.sectionSchema].join("\n\n"),
    ["## Table Configuration Documentation", resources.docsTableConfig].join("\n\n"),
    ["## Advanced Configuration Examples", resources.docsAdvancedExamples].join("\n\n"),
    ["## Tutorial Reference", resources.docsTutorial].join("\n\n"),
    ["## Example Without Sections", resources.exampleNoSections].join("\n\n"),
    ["## Example With Sections", resources.exampleWithSections].join("\n\n"),
  ];
}

export function createSystemPromptHook(cache: TablassistCache): NonNullable<Hooks["experimental.chat.system.transform"]> {
  return async (_input, output) => {
    const resources = await cache.getSystemPromptResources();
    output.system.push(...formatSystemPromptResources(resources));
  };
}
