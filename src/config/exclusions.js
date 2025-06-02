export const DEFAULT_EXCLUSIONS = [
  // Python
  '__pycache__',
  '*.pyc',
  '*.pyo',
  '*.pyd',
  '.Python',
  'build',
  'develop-eggs',
  'dist',
  'downloads',
  'eggs',
  '.eggs',
  'lib',
  'lib64',
  'parts',
  'sdist',
  'var',
  'wheels',
  '*.egg-info',
  '.installed.cfg',
  '*.egg',
  
  // Version Control
  '.git',
  '.gitignore',
  '.gitattributes',
  '.gitmodules',
  '.svn',
  '.hg',
  
  // IDEs
  '.idea',
  '.vscode', 
  '.cursor',
  '*.swp',
  '*.swo',
  '*~',
  
  // Testing/Cache
  '.pytest_cache',
  '.coverage',
  '.nyc_output',
  '.cache',
  'htmlcov',
  '.tox',
  '.nox',
  
  // Node.js
  'node_modules',
  'npm-debug.log*',
  'yarn-debug.log*',
  'yarn-error.log*',
  '.npm',
  '.yarn-integrity',
  
  // Virtual Environments
  'venv',
  '.venv', 
  'env',
  '.env',
  'virtualenv',
  'ENV',
  'env.bak',
  'venv.bak',
  
  // Build/Dist
  'target',
  'out',
  'bin',
  'obj',
  
  // OS
  '.DS_Store',
  '.DS_Store?',
  '._*',
  '.Spotlight-V100',
  '.Trashes',
  'ehthumbs.db',
  'Thumbs.db',
  'Desktop.ini',
  
  // Logs
  '*.log',
  'logs',
  
  // Temporary files
  '*.tmp',
  '*.temp',
  '.tmp',
  '.temp',
  
  // Documentation build outputs
  '_build',
  'site',
  '.jekyll-cache',
  
  // Package managers
  'Pipfile.lock',
  'poetry.lock',
  'package-lock.json',
  'yarn.lock'
]; 