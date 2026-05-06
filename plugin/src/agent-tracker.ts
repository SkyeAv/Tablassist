import type { Hooks } from "@opencode-ai/plugin"

import type { CachedResourceKey } from "./cache.ts"

/**
 * Agent-specific system-prompt resource bundles.
 */
export const RESOURCE_AGENT_KEYS: Record<string, CachedResourceKey[]> = {
  "the-builder": ["sectionSchema", "docsTableConfig"],
  "the-configurator": ["docsTableConfig"],
  "the-pioneer": ["docsTableConfig"],
}

export function createAgentTracker() {
  const sessionAgents = new Map<string, string>()

  function track(sessionID: string, agent: string): void {
    sessionAgents.set(sessionID, agent)
  }

  function get(sessionID: string | undefined): string | undefined {
    if (!sessionID) return undefined
    return sessionAgents.get(sessionID)
  }

  function getPromptResourceKeys(sessionID: string | undefined): CachedResourceKey[] {
    const agent = get(sessionID)
    if (!agent) return []
    return RESOURCE_AGENT_KEYS[agent] ?? []
  }

  function needsResources(sessionID: string | undefined): boolean {
    return getPromptResourceKeys(sessionID).length > 0
  }

  return { track, get, getPromptResourceKeys, needsResources }
}

export type AgentTracker = ReturnType<typeof createAgentTracker>

export function createAgentTrackingHook(tracker: AgentTracker): NonNullable<Hooks["chat.params"]> {
  return async (input, _output) => {
    tracker.track(input.sessionID, input.agent)
  }
}
