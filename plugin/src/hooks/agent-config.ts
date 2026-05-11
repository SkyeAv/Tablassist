import { readFile, readdir } from "node:fs/promises"
import { basename, join } from "node:path"

import type { Hooks } from "@opencode-ai/plugin"
import type { AgentConfig } from "@opencode-ai/sdk"

const AGENTS_DIR = join(import.meta.dir, "..", "..", "agents")

interface AgentFrontmatter {
  description: string
  mode: "primary" | "subagent" | "all"
  color?: string
  temperature?: number
  maxSteps?: number
  tools?: { [key: string]: boolean }
  permission?: {
    edit?: "ask" | "allow" | "deny"
    bash?: "ask" | "allow" | "deny"
    webfetch?: "ask" | "allow" | "deny"
    doom_loop?: "ask" | "allow" | "deny"
    external_directory?: "ask" | "allow" | "deny"
  }
}

function parseFrontmatter(content: string): { frontmatter: AgentFrontmatter; body: string } | null {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/)
  if (!match) return null

  const yamlBlock = match[1]
  const body = match[2]
  if (yamlBlock === undefined || body === undefined) return null

  const frontmatter: Record<string, unknown> = {}

  // Parse YAML frontmatter — supports flat scalars and one-level nested objects
  let currentKey: string | null = null
  let currentObj: Record<string, string> | null = null

  for (const line of yamlBlock.split("\n")) {
    const trimmed = line.trimEnd()
    if (!trimmed || trimmed.startsWith("#")) continue

    const nestedMatch = trimmed.match(/^(\s{2,})([\w-]+):\s*(.+)$/)
    if (nestedMatch && currentKey && currentObj) {
      const nestedKey = nestedMatch[2]
      const nestedValue = nestedMatch[3]
      if (nestedKey !== undefined && nestedValue !== undefined) {
        currentObj[nestedKey] = nestedValue.trim()
      }
      continue
    }

    // Flush any pending nested object
    if (currentKey && currentObj) {
      frontmatter[currentKey] = currentObj
      currentKey = null
      currentObj = null
    }

    const scalarMatch = trimmed.match(/^(\w[\w-]*):\s+(.+)$/)
    if (scalarMatch) {
      const key = scalarMatch[1]
      const raw = scalarMatch[2]
      if (key !== undefined && raw !== undefined) {
        let value = raw.trim()
        if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
          value = value.slice(1, -1)
        }
        const num = Number(value)
        frontmatter[key] = Number.isFinite(num) && value !== "" ? num : value
      }
      continue
    }

    const objectStart = trimmed.match(/^(\w[\w-]*):\s*$/)
    if (objectStart) {
      const key = objectStart[1]
      if (key !== undefined) {
        currentKey = key
        currentObj = {}
      }
    }
  }

  // Flush trailing nested object
  if (currentKey && currentObj) {
    frontmatter[currentKey] = currentObj
  }

  if (!frontmatter.description || !frontmatter.mode) return null

  return {
    frontmatter: frontmatter as unknown as AgentFrontmatter,
    body: body.trim(),
  }
}

async function loadAgentFiles(): Promise<Map<string, AgentConfig>> {
  const agents = new Map<string, AgentConfig>()

  let entries: string[]
  try {
    const dirEntries = await readdir(AGENTS_DIR)
    entries = dirEntries.filter((f) => f.endsWith(".md"))
  } catch {
    return agents
  }

  for (const filename of entries) {
    const filePath = join(AGENTS_DIR, filename)
    const content = await readFile(filePath, "utf-8")
    const parsed = parseFrontmatter(content)
    if (!parsed) continue

    const name = basename(filename, ".md")
    const { frontmatter, body } = parsed

    const agentConfig: AgentConfig = {
      description: frontmatter.description,
      mode: frontmatter.mode,
      prompt: body,
    }

    if (frontmatter.color !== undefined) {
      agentConfig.color = frontmatter.color
    }

    if (frontmatter.temperature !== undefined) {
      agentConfig.temperature = frontmatter.temperature
    }

    if (frontmatter.maxSteps !== undefined) {
      agentConfig.maxSteps = frontmatter.maxSteps
    }

    if (frontmatter.tools) {
      const toolsMap: { [key: string]: boolean } = {}
      for (const [toolName, value] of Object.entries(frontmatter.tools)) {
        toolsMap[toolName] = typeof value === "boolean" ? value : String(value) === "true"
      }
      agentConfig.tools = toolsMap
    }

    if (frontmatter.permission) {
      agentConfig.permission = { ...frontmatter.permission }
    }

    agents.set(name, agentConfig)
  }

  return agents
}

export function createAgentConfigHook(): NonNullable<Hooks["config"]> {
  return async (config) => {
    const agents = await loadAgentFiles()
    if (agents.size === 0) return

    const existing = (config.agent ?? {}) as Record<string, AgentConfig | undefined>

    for (const [name, agentConfig] of agents) {
      existing[name] = agentConfig
    }

    config.agent = existing
  }
}
