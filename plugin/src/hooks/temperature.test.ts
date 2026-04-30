import { describe, expect, it } from "bun:test"

import { FALLBACK_TEMPERATURE, createTemperatureHook } from "./temperature.ts"

type ChatParamsInput = Parameters<ReturnType<typeof createTemperatureHook>>[0]
type ChatParamsOutput = Parameters<ReturnType<typeof createTemperatureHook>>[1]

function makeInput(temperatureCapable: boolean): ChatParamsInput {
  return {
    model: { capabilities: { temperature: temperatureCapable } },
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

  it("leaves temperature unchanged when model supports temperature", async () => {
    const hook = createTemperatureHook()
    const output = makeOutput(0.3)
    await hook(makeInput(true), output)
    expect(output.temperature).toBe(0.3)
  })
})

describe("FALLBACK_TEMPERATURE", () => {
  it("is 1", () => {
    expect(FALLBACK_TEMPERATURE).toBe(1)
  })
})
