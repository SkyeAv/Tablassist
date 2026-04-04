import type { Hooks } from "@opencode-ai/plugin"

/**
 * Agents that receive all system prompt resources (schema, docs, examples).
 * All other agents receive nothing.
 */
export const RESOURCE_AGENTS = new Set(["the-builder", "the-configurator"])

export function createAgentTracker() {
  const sessionAgents = new Map<string, string>()

  function track(sessionID: string, agent: string): void {
    sessionAgents.set(sessionID, agent)
  }

  function get(sessionID: string | undefined): string | undefined {
    if (!sessionID) return undefined
    return sessionAgents.get(sessionID)
  }

  function needsResources(sessionID: string | undefined): boolean {
    const agent = get(sessionID)
    if (!agent) return true // Fallback: inject all resources when unknown
    return RESOURCE_AGENTS.has(agent)
  }

  return { track, get, needsResources }
}

export type AgentTracker = ReturnType<typeof createAgentTracker>

export function createAgentTrackingHook(tracker: AgentTracker): NonNullable<Hooks["chat.params"]> {
  return async (input, _output) => {
    tracker.track(input.sessionID, input.agent)
  }
}
