import { describe, expect, it } from "bun:test"

import { FALLBACK_TEMPERATURE, createTemperatureHook } from "./temperature.ts"

type ChatParamsInput = Parameters<ReturnType<typeof createTemperatureHook>>[0]
type ChatParamsOutput = Parameters<ReturnType<typeof createTemperatureHook>>[1]

function makeInput(
  temperatureCapable: boolean,
  id = "some-model",
  options: Record<string, unknown> = {},
): ChatParamsInput {
  return {
    model: { id, capabilities: { temperature: temperatureCapable }, options },
  } as unknown as ChatParamsInput
}

function makeOutput(temperature: number): ChatParamsOutput {
  return { temperature, topP: 1, topK: 0, options: {} }
}

describe("createTemperatureHook", () => {
  it("coerces temperature to fallback when model lacks temperature capability", async () => {
    const hook = createTemperatureHook()
    const output = makeOutput(0.3)
    await hook(makeInput(false), output)
    expect(output.temperature).toBe(FALLBACK_TEMPERATURE)
  })

  it("leaves temperature unchanged for normal capable models", async () => {
    const hook = createTemperatureHook()
    const output = makeOutput(0.3)
    await hook(makeInput(true), output)
    expect(output.temperature).toBe(0.3)
  })

  it("overrides temperature to 1 for kimi-k2.6", async () => {
    const hook = createTemperatureHook()
    const output = makeOutput(0.3)
    await hook(makeInput(true, "kimi-k2.6"), output)
    expect(output.temperature).toBe(1)
  })

  it("respects model.options.temperature over ID map", async () => {
    const hook = createTemperatureHook()
    const output = makeOutput(0.3)
    await hook(makeInput(true, "kimi-k2.6", { temperature: 0.5 }), output)
    expect(output.temperature).toBe(0.5)
  })

  it("does not override when temperature already matches fixed value", async () => {
    const hook = createTemperatureHook()
    const output = makeOutput(1)
    await hook(makeInput(true, "kimi-k2.6"), output)
    expect(output.temperature).toBe(1)
  })
})

describe("FALLBACK_TEMPERATURE", () => {
  it("is 1", () => {
    expect(FALLBACK_TEMPERATURE).toBe(1)
  })
})
