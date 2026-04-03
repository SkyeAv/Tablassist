import type { PluginInput } from "@opencode-ai/plugin";

export type CliRunner = (command: string, args: string[]) => Promise<string>;
export type CliDetailedRunner = (
  command: string,
  args: string[],
) => Promise<CliCommandResult>;

export type CliCommandResult = {
  command: string;
  args: string[];
  exitCode: number;
  stdout: string;
  stderr: string;
};

export async function runCliDetailed(
  shell: PluginInput["$"],
  command: string,
  args: string[],
): Promise<CliCommandResult> {
  const shellCommand = ["tablassist", command, ...args]
    .map((part) => shell.escape(part))
    .join(" ");
  const output = await shell.nothrow()`${{ raw: shellCommand }}`.quiet();

  return {
    command,
    args,
    exitCode: output.exitCode,
    stdout: output.stdout.toString("utf8").trim(),
    stderr: output.stderr.toString("utf8").trim(),
  };
}

export async function runCliCommand(
  shell: PluginInput["$"],
  command: string,
  args: string[],
): Promise<string> {
  const result = await runCliDetailed(shell, command, args);

  if (result.exitCode !== 0) {
    return result.stderr || result.stdout || `Command failed: ${command}`;
  }

  return result.stdout;
}
