import { tool } from "@opencode-ai/plugin"
import type { ZodType } from "zod"

import { CLI_ERROR_PREFIX } from "../cli.ts"

type ToolArgsShape = Record<string, ZodType>

export function createCliTool<Args extends Record<string, unknown>>(
  description: string,
  args: ToolArgsShape,
  execute: (args: Args) => Promise<string>,
) {
  return tool({
    description,
    args,
    async execute(input, context) {
      const result = await execute(input as Args)
      const isError = result.startsWith(CLI_ERROR_PREFIX)
      context.metadata({ title: isError ? `Error: ${description}` : description })
      return result
    },
  })
}
