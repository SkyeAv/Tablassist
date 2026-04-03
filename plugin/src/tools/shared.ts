import { tool } from "@opencode-ai/plugin";
import type { ZodType } from "zod";

type ToolArgsShape = Record<string, ZodType>;

export function createCliTool<Args extends Record<string, unknown>>(
  description: string,
  args: ToolArgsShape,
  execute: (args: Args) => Promise<string>,
) {
  return tool({
    description,
    args,
    async execute(input, context) {
      context.metadata({ title: description });
      return execute(input as Args);
    },
  });
}
