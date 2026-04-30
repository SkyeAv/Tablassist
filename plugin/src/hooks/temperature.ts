import type { Hooks } from "@opencode-ai/plugin"

export const FALLBACK_TEMPERATURE = 1

// Models that accept the temperature param but only allow a specific fixed value
const FIXED_TEMPERATURE_MODELS: Record<string, number> = {
  "kimi-k2.6": 1,
}

export function createTemperatureHook(): NonNullable<Hooks["chat.params"]> {
  return async (input, output) => {
    if (!input.model.capabilities.temperature) {
      output.temperature = FALLBACK_TEMPERATURE
      return
    }

    // options.temperature takes priority; fall back to known restricted model IDs
    const fixedTemp =
      typeof (input.model.options as Record<string, unknown>)?.temperature === "number"
        ? ((input.model.options as Record<string, unknown>).temperature as number)
        : FIXED_TEMPERATURE_MODELS[input.model.id]

    if (fixedTemp !== undefined && output.temperature !== fixedTemp) {
      output.temperature = fixedTemp
    }
  }
}
