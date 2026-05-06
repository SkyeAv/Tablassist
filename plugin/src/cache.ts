export type CachedResourceKey =
  | "sectionSchema"
  | "docsTableConfig"

export type CachedResourceMap = Record<CachedResourceKey, string>

export type CacheLoader = (command: string, args: string[]) => Promise<string>

const RESOURCE_COMMANDS: Record<CachedResourceKey, string> = {
  sectionSchema: "section-schema",
  docsTableConfig: "docs-table-config",
}

export function createTablassistCache(loader: CacheLoader) {
  const values = new Map<CachedResourceKey, string>()
  const pending = new Map<CachedResourceKey, Promise<string>>()

  async function get(key: CachedResourceKey): Promise<string> {
    const existing = values.get(key)
    if (existing !== undefined) {
      return existing
    }

    const current = pending.get(key)
    if (current) {
      return current
    }

    const request = loader(RESOURCE_COMMANDS[key], [])
      .then((value) => {
        values.set(key, value)
        pending.delete(key)
        return value
      })
      .catch((error) => {
        pending.delete(key)
        throw error
      })

    pending.set(key, request)
    return request
  }

  async function getSystemPromptResources(): Promise<CachedResourceMap> {
    const [sectionSchema, docsTableConfig] = await Promise.all([get("sectionSchema"), get("docsTableConfig")])

    return {
      sectionSchema,
      docsTableConfig,
    }
  }

  return {
    get,
    getSystemPromptResources,
  }
}

export type TablassistCache = ReturnType<typeof createTablassistCache>
