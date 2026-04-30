import type { Hooks } from "@opencode-ai/plugin"

export const FALLBACK_TEMPERATURE = 1

export function createTemperatureHook(): NonNullable<Hooks["chat.params"]> {
  return async (input, output) => {
    if (!input.model.capabilities.temperature) {
      output.temperature = FALLBACK_TEMPERATURE
    }
  }
}
