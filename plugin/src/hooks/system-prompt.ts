import type { Hooks } from "@opencode-ai/plugin"

import type { AgentTracker } from "../agent-tracker.ts"
import type { CachedResourceKey, CachedResourceMap, TablassistCache } from "../cache.ts"

const RESOURCE_HEADERS: Record<CachedResourceKey, string> = {
  sectionSchema: "## Tablassert Section JSON Schema",
  docsTableConfig: "## Table Configuration Documentation",
}

export function formatSystemPromptResources(
  resources: Partial<CachedResourceMap>,
  keys: CachedResourceKey[],
): string[] {
  return keys.flatMap((key) => {
    const value = resources[key]
    if (!value) return []
    return [[RESOURCE_HEADERS[key], value].join("\n\n")]
  })
}

export function createSystemPromptHook(
  cache: TablassistCache,
  tracker: AgentTracker,
): NonNullable<Hooks["experimental.chat.system.transform"]> {
  return async (input, output) => {
    const keys = tracker.getPromptResourceKeys(input.sessionID)
    if (keys.length === 0) return

    const entries = await Promise.all(keys.map(async (key) => [key, await cache.get(key)] as const))
    const resources = Object.fromEntries(entries) as Partial<CachedResourceMap>

    output.system.push(...formatSystemPromptResources(resources, keys))
  }
}
