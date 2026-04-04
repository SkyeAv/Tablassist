import { describe, expect, it } from "bun:test"

import { CLI_ERROR_PREFIX } from "./cli.ts"

describe("CLI_ERROR_PREFIX", () => {
  it("is a consistent prefix string", () => {
    expect(CLI_ERROR_PREFIX).toBe("ERROR: ")
  })
})

describe("error prefix detection", () => {
  it("can be detected with startsWith", () => {
    const errorResult = `${CLI_ERROR_PREFIX}something went wrong`
    expect(errorResult.startsWith(CLI_ERROR_PREFIX)).toBe(true)
  })

  it("does not match normal output", () => {
    const normalResult = '{"status": "ok"}'
    expect(normalResult.startsWith(CLI_ERROR_PREFIX)).toBe(false)
  })

  it("does not match output that merely contains the word error", () => {
    const output = '{"error": "validation failed"}'
    expect(output.startsWith(CLI_ERROR_PREFIX)).toBe(false)
  })
})
