import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { generateClassDiagram } from './tools/class-diagram.js';
import { generateTreeStructure } from './tools/tree-structure.js';
import { generateModuleFunctions } from './tools/module-functions.js';

export class DocsToolServer {
  constructor() {
    this.server = new McpServer({
      name: 'docs-tools',
      version: '1.0.0'
    });
    this.setupTools();
  }

  setupTools() {
    // Tool 1: create_class_diagram
    this.server.tool(
      'create_class_diagram',
      {
        project_path: z.string().describe('Root path of the Python project to analyze')
      },
      async ({ project_path }) => {
        try {
          return await generateClassDiagram(project_path);
        } catch (error) {
          return {
            content: [{
              type: 'text',
              text: `Error generating class diagram: ${error.message}`
            }],
            isError: true
          };
        }
      }
    );

    // Tool 2: create_tree_structure
    this.server.tool(
      'create_tree_structure',
      {
        project_path: z.string().describe('Root path of the project to analyze')
      },
      async ({ project_path }) => {
        try {
          return await generateTreeStructure(project_path);
        } catch (error) {
          return {
            content: [{
              type: 'text',
              text: `Error generating tree structure: ${error.message}`
            }],
            isError: true
          };
        }
      }
    );

    // Tool 3: create_module_functions
    this.server.tool(
      'create_module_functions',
      {
        project_path: z.string().describe('Root path of the Python project to analyze')
      },
      async ({ project_path }) => {
        try {
          return await generateModuleFunctions(project_path);
        } catch (error) {
          return {
            content: [{
              type: 'text',
              text: `Error generating module functions: ${error.message}`
            }],
            isError: true
          };
        }
      }
    );
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
} 