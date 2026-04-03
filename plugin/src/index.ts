import type { Plugin } from "@opencode-ai/plugin";

import { createTablassistCache } from "./cache.ts";
import { runCliCommand, runCliDetailed } from "./cli.ts";
import { createSystemPromptHook } from "./hooks/system-prompt.ts";
import { createYamlValidationHook } from "./hooks/yaml-validation.ts";
import { createAllTools } from "./tools/index.ts";

const Tablassist: Plugin = async ({ $ }) => {
  const cli = (command: string, args: string[]) => runCliCommand($, command, args);
  const cliDetailed = (command: string, args: string[]) => runCliDetailed($, command, args);
  const cache = createTablassistCache(cli);

  return {
    tool: createAllTools(cli),
    "tool.execute.after": createYamlValidationHook(cliDetailed),
    "experimental.chat.system.transform": createSystemPromptHook(cache),
  };
};

export default Tablassist;
