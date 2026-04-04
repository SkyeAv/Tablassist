import type { Plugin } from "@opencode-ai/plugin"

import { createAgentTracker, createAgentTrackingHook } from "./agent-tracker.ts"
import { createTablassistCache } from "./cache.ts"
import { runCliCommand, runCliDetailed } from "./cli.ts"
import { createAgentConfigHook } from "./hooks/agent-config.ts"
import { createCommandConfigHook } from "./hooks/command-config.ts"
import { createSystemPromptHook } from "./hooks/system-prompt.ts"
import { createYamlValidationHook } from "./hooks/yaml-validation.ts"
import { createAllTools } from "./tools/index.ts"

const Tablassist: Plugin = async ({ $ }) => {
  const cli = (command: string, args: string[]) => runCliCommand($, command, args)
  const cliDetailed = (command: string, args: string[]) => runCliDetailed($, command, args)
  const cache = createTablassistCache(cli)
  const tracker = createAgentTracker()

  const agentConfigHook = createAgentConfigHook()
  const commandConfigHook = createCommandConfigHook()

  return {
    config: async (config) => {
      await agentConfigHook(config)
      await commandConfigHook(config)
    },
    tool: createAllTools(cli),
    "chat.params": createAgentTrackingHook(tracker),
    "tool.execute.after": createYamlValidationHook(cliDetailed),
    "experimental.chat.system.transform": createSystemPromptHook(cache, tracker),
  }
}

export default Tablassist
