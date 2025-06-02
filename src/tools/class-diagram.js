import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { promises as fs } from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export async function generateClassDiagram(projectPath) {
  return new Promise((resolve, reject) => {
    // Validate project path
    if (!projectPath || typeof projectPath !== 'string') {
      reject(new Error('Invalid project path provided'));
      return;
    }

    const pythonScript = path.join(__dirname, '../../python/generate_uml.py');
    const docsDir = path.join(projectPath, 'docs');
    
    // Check if Python script exists
    fs.access(pythonScript, fs.constants.F_OK)
      .then(() => {
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
            const umlPath = path.join(docsDir, 'uml.txt');
            resolve({
              content: [{
                type: 'text',
                text: `Class diagram generated successfully!\n\nOutput file: ${umlPath}\n\n${stdout.trim()}`
              }]
            });
          } else {
            reject(new Error(`Python process failed with code ${code}: ${stderr.trim() || stdout.trim()}`));
          }
        });

        pythonProcess.on('error', (error) => {
          reject(new Error(`Failed to start Python process: ${error.message}`));
        });
      })
      .catch((error) => {
        reject(new Error(`Python script not found: ${pythonScript}`));
      });
  });
} 