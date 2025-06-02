# Node.js MCP Tool Server Design Document

## Overview
A Node.js-based MCP (Model Context Protocol) tool server that provides three focused documentation generation tools. Built as an npm package that can be run with `npx`, making it easily distributable and executable without complex setup.

## Core Functionality

### Exposed MCP Tools
1. **create_class_diagram** - Analyzes Python files and generates UML class diagrams
2. **create_tree_structure** - Creates directory tree structure documentation  
3. **create_module_functions** - Documents module-level functions and their signatures

## Architecture

### Project Structure
```
mcp-docs-tools/
├── package.json
├── bin/
│   └── server.js              # Main MCP server entry point
├── src/
│   ├── server.js              # MCP server implementation
│   ├── tools/
│   │   ├── class-diagram.js   # Python AST parsing for classes
│   │   ├── tree-structure.js  # Directory tree generation
│   │   └── module-functions.js # Function parsing and documentation
│   ├── parsers/
│   │   ├── python-ast.js      # Python AST parsing utilities
│   │   └── file-utils.js      # File I/O and filtering utilities
│   └── config/
│       └── exclusions.js      # Default exclusion patterns
├── python/
│   ├── ast_parser.py          # Python script for AST parsing
│   └── requirements.txt       # Python dependencies
└── README.md
```

## Tool Specifications

### 1. create_class_diagram
**Purpose**: Generate UML class diagrams from Python code

**MCP Tool Definition**:
```json
{
  "name": "create_class_diagram",
  "description": "Analyze Python files and generate PlantUML class diagrams showing classes, methods, and attributes",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_path": {
        "type": "string",
        "description": "Root path of the Python project to analyze"
      }
    },
    "required": ["project_path"]
  }
}
```

**Output**: 
- File: `docs/uml.txt`
- Format: PlantUML syntax
- Content: Classes with public/private methods and attributes

### 2. create_tree_structure  
**Purpose**: Generate project directory tree structure

**MCP Tool Definition**:
```json
{
  "name": "create_tree_structure",
  "description": "Generate a visual directory tree structure excluding cache, build, and IDE files",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_path": {
        "type": "string", 
        "description": "Root path of the project to analyze"
      }
    },
    "required": ["project_path"]
  }
}
```

**Output**:
- File: `docs/tree-structure.txt`  
- Format: Unicode box-drawing tree
- Content: Complete file/directory structure with exclusions

### 3. create_module_functions
**Purpose**: Document module-level functions and signatures

**MCP Tool Definition**:
```json
{
  "name": "create_module_functions", 
  "description": "Analyze Python files and document module-level functions with parameters, return types, and decorators",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_path": {
        "type": "string",
        "description": "Root path of the Python project to analyze"
      }
    },
    "required": ["project_path"]
  }
}
```

**Output**:
- File: `docs/module-functions.txt`
- Format: Hierarchical text documentation
- Content: Functions organized by package/module with full signatures

## Implementation Strategy

### Node.js + Python Hybrid Approach
Since the existing code is in Python and provides robust AST parsing, the Node.js server will:

1. **Orchestrate execution** - Handle MCP protocol and tool routing
2. **Spawn Python processes** - Execute Python scripts for actual parsing
3. **Manage file I/O** - Handle output file creation and path management
4. **Provide consistent interface** - Expose clean MCP tool interfaces

### Core Server Implementation
```javascript
// src/server.js
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';

class DocsToolServer {
  constructor() {
    this.server = new Server(
      { name: 'docs-tools', version: '1.0.0' },
      { capabilities: { tools: {} } }
    );
    this.setupTools();
  }

  setupTools() {
    // Register the three tools
    this.server.setRequestHandler('tools/list', async () => ({
      tools: [
        {
          name: 'create_class_diagram',
          description: 'Generate UML class diagrams from Python code',
          inputSchema: {
            type: 'object',
            properties: {
              project_path: { type: 'string', description: 'Root path of Python project' }
            },
            required: ['project_path']
          }
        },
        {
          name: 'create_tree_structure', 
          description: 'Generate visual directory tree structure',
          inputSchema: {
            type: 'object',
            properties: {
              project_path: { type: 'string', description: 'Root path of project' }
            },
            required: ['project_path']
          }
        },
        {
          name: 'create_module_functions',
          description: 'Document module-level functions with signatures',
          inputSchema: {
            type: 'object',
            properties: {
              project_path: { type: 'string', description: 'Root path of Python project' }
            },
            required: ['project_path']
          }
        }
      ]
    }));

    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      switch (name) {
        case 'create_class_diagram':
          return await this.createClassDiagram(args.project_path);
        case 'create_tree_structure':
          return await this.createTreeStructure(args.project_path);
        case 'create_module_functions':
          return await this.createModuleFunctions(args.project_path);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }
}
```

### Python Script Execution
```javascript
// src/tools/class-diagram.js
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export async function generateClassDiagram(projectPath) {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(__dirname, '../../python/generate_uml.py');
    const docsDir = path.join(projectPath, 'docs');
    
    const pythonProcess = spawn('python3', [
      pythonScript,
      '--root', projectPath,
      '--output', docsDir,
      '--uml-only'
    ]);

    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        resolve({
          content: [{
            type: 'text',
            text: `Class diagram generated successfully at ${path.join(docsDir, 'uml.txt')}\n${stdout}`
          }]
        });
      } else {
        reject(new Error(`Python process failed: ${stderr}`));
      }
    });
  });
}
```

## Python Scripts (Adapted from Your Code)

### generate_uml.py
Streamlined version of your `build_uml_diagram.py`:
```python
#!/usr/bin/env python3
import os
import ast
import argparse
import sys
from collections import Counter

# [Include your UMLClassVisitor and related functions]
# Modifications:
# - Remove site content functionality  
# - Remove module functions (separate script)
# - Fixed output to docs/uml.txt
# - Add --uml-only flag

def main():
    parser = argparse.ArgumentParser(description="Generate UML class diagrams")
    parser.add_argument("--root", required=True, help="Root directory")
    parser.add_argument("--output", required=True, help="Output directory") 
    parser.add_argument("--uml-only", action="store_true", help="Generate only UML")
    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Generate UML
    packages = parse_directory(args.root)
    uml_source = generate_plantuml(packages)
    
    uml_path = os.path.join(args.output, "uml.txt")
    with open(uml_path, "w", encoding="utf-8") as f:
        f.write(uml_source)
    
    print(f"UML diagram saved to: {uml_path}")

if __name__ == "__main__":
    main()
```

### generate_functions.py  
Extracted from your `build_uml_diagram.py`:
```python
#!/usr/bin/env python3
# [Include module function parsing code from your build_uml_diagram.py]
# Modifications:
# - Extract only module function functionality
# - Fixed output to docs/module-functions.txt
# - Remove class parsing
```

### generate_tree.py
Adapted from your `update_tree.py`:
```python  
#!/usr/bin/env python3
import os
import argparse

# [Include your tree generation functions]
# Modifications:
# - Remove logger dependency
# - Remove README integration
# - Fixed output to docs/tree-structure.txt
# - Enhanced exclusions list

DEFAULT_EXCLUSIONS = [
    '__pycache__', '.git', '.idea', '.pytest_cache', 
    '.cursor', '.vscode', 'node_modules', 'venv', 
    '.venv', 'env', 'virtualenv', 'dist', 'build'
]

def main():
    parser = argparse.ArgumentParser(description="Generate directory tree")
    parser.add_argument("--root", required=True, help="Root directory")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    
    tree_content = generate_tree(args.root, DEFAULT_EXCLUSIONS)
    tree_content = clean_tree_content(tree_content)
    
    tree_path = os.path.join(args.output, "tree-structure.txt") 
    with open(tree_path, "w", encoding="utf-8") as f:
        f.write(tree_content)
    
    print(f"Tree structure saved to: {tree_path}")
```

## Package Configuration

### package.json
```json
{
  "name": "mcp-docs-tools",
  "version": "1.0.0", 
  "description": "MCP tools for generating project documentation",
  "type": "module",
  "bin": {
    "mcp-docs-tools": "./bin/server.js"
  },
  "main": "./src/server.js",
  "scripts": {
    "start": "node bin/server.js",
    "dev": "node bin/server.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "latest"
  },
  "engines": {
    "node": ">=18.0.0"
  },
  "keywords": ["mcp", "documentation", "uml", "python", "ast"],
  "author": "Your Name",
  "license": "MIT",
  "files": [
    "bin/",
    "src/", 
    "python/",
    "README.md"
  ]
}
```

### bin/server.js
```javascript
#!/usr/bin/env node
import { DocsToolServer } from '../src/server.js';

const server = new DocsToolServer();
server.run().catch(console.error);
```

## File Exclusion Logic

### Default Exclusions
```javascript
// src/config/exclusions.js
export const DEFAULT_EXCLUSIONS = [
  // Python
  '__pycache__',
  '*.pyc',
  '*.pyo',
  
  // Version Control
  '.git',
  '.gitignore',
  
  // IDEs
  '.idea',
  '.vscode', 
  '.cursor',
  
  // Testing/Cache
  '.pytest_cache',
  '.coverage',
  
  // Node.js
  'node_modules',
  
  // Virtual Environments
  'venv',
  '.venv', 
  'env',
  'virtualenv',
  
  // Build/Dist
  'dist',
  'build',
  'target',
  
  // OS
  '.DS_Store',
  'Thumbs.db'
];
```

## Usage and Distribution

### Installation and Usage
```bash
# Install globally
npm install -g mcp-docs-tools

# Or run directly with npx
npx mcp-docs-tools

# Or run from local directory  
npm start
```

### MCP Tool Integration
Once running, the server exposes three tools that can be called via MCP:

1. `create_class_diagram` - Generates `docs/uml.txt`
2. `create_tree_structure` - Generates `docs/tree-structure.txt`  
3. `create_module_functions` - Generates `docs/module-functions.txt`

### Cursor Integration
Create `.cursorrules` file in projects:
```markdown
# Documentation Tools Integration

## Available MCP Tools
- `create_class_diagram` - Generate UML class diagrams  
- `create_tree_structure` - Generate directory tree
- `create_module_functions` - Document module functions

## Usage
Run these tools at session start to generate documentation in `docs/` directory.
Reference the generated files to understand codebase structure and avoid redundancy.

## Generated Files
- `docs/uml.txt` - PlantUML class diagrams
- `docs/tree-structure.txt` - Directory structure  
- `docs/module-functions.txt` - Function documentation
```

## Implementation Benefits

### Advantages of Node.js Approach
- **Simple Distribution**: Single `npx` command installation
- **No Complex Dependencies**: Leverages existing Python code via process spawning
- **Clean Separation**: Node.js handles MCP protocol, Python handles parsing
- **Easy Maintenance**: Focused tools with clear responsibilities
- **Cross-Platform**: Works on any system with Node.js and Python

### Error Handling Strategy
- **Python Process Failures**: Capture stderr and return meaningful error messages
- **Missing Dependencies**: Check for Python availability on startup
- **File Permission Issues**: Graceful handling with clear error reporting
- **Invalid Project Paths**: Validate paths before processing

### Performance Considerations
- **Process Overhead**: Minimal since tools are run on-demand
- **File I/O**: Efficient with Node.js async file operations
- **Memory Usage**: Low footprint as Python processes are short-lived
- **Caching**: Can be added later if needed for large projects

This design provides a clean, focused solution that leverages your existing Python code while providing a simple Node.js-based MCP interface that's easy to distribute and use with `npx`.
