import { spawnSync } from 'child_process';
import os from 'os';

// Cache detection for process lifetime
let cachedInvocation = null;

function parsePythonVersion(output) {
  if (!output) return null;
  const match = /Python\s+(\d+)\.(\d+)\.(\d+)/i.exec(output);
  if (!match) return null;
  const major = parseInt(match[1], 10);
  const minor = parseInt(match[2], 10);
  const patch = parseInt(match[3], 10);
  return { major, minor, patch };
}

function isPython3(command, args) {
  const result = spawnSync(command, [...(args || []), '--version'], { encoding: 'utf8' });
  const combined = `${result.stdout || ''} ${result.stderr || ''}`.trim();
  const version = parsePythonVersion(combined);
  return version && version.major >= 3;
}

function getPlatformCandidates() {
  const isWindows = os.platform() === 'win32';
  if (isWindows) {
    return [
      { command: 'py', args: ['-3'] },
      { command: 'python', args: [] },
      { command: 'python3', args: [] },
    ];
  }
  return [
    { command: 'python3', args: [] },
    { command: 'python', args: [] },
  ];
}

export function getPythonInvocation() {
  if (cachedInvocation) return cachedInvocation;

  // Environment overrides
  const envCmd = process.env.MCP_PYTHON && process.env.MCP_PYTHON.trim();
  const envArgs = (process.env.MCP_PYTHON_ARGS || '')
    .split(' ')
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  const tried = [];

  if (envCmd) {
    tried.push(`${envCmd} ${envArgs.join(' ')}`.trim());
    if (isPython3(envCmd, envArgs)) {
      cachedInvocation = { command: envCmd, args: envArgs };
      return cachedInvocation;
    }
  }

  const candidates = getPlatformCandidates();
  for (const { command, args } of candidates) {
    tried.push(`${command} ${args.join(' ')}`.trim());
    if (isPython3(command, args)) {
      cachedInvocation = { command, args };
      return cachedInvocation;
    }
  }

  const triedMsg = tried.join(', ');
  const guidance = 'Install Python 3 from https://www.python.org/downloads/ or set MCP_PYTHON (and optional MCP_PYTHON_ARGS).';
  const err = new Error(`Python 3 interpreter not found. ${guidance} Tried: ${triedMsg}`);
  err.code = 'PYTHON3_NOT_FOUND';
  throw err;
}

export function formatPythonNotFoundError(error, triedFallback) {
  const triedText = Array.isArray(triedFallback) && triedFallback.length > 0
    ? ` Tried: ${triedFallback.join(', ')}`
    : '';
  const base = 'Python 3 interpreter not found. Install Python 3 or set MCP_PYTHON (and optional MCP_PYTHON_ARGS).';
  const msg = `${base}${triedText}`;
  const e = new Error(msg);
  e.code = 'PYTHON3_NOT_FOUND';
  if (error && error.message) {
    e.cause = error;
  }
  return e;
}

// intentionally removed; user requested design doc only, no code changes


