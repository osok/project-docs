#!/usr/bin/env python3
"""
Generate directory tree structure documentation.
Adapted for MCP tool server usage.
"""

import os
import argparse
import sys
from typing import List, Set


DEFAULT_EXCLUSIONS = [
    '__pycache__', '.git', '.idea', '.pytest_cache', 
    '.cursor', '.vscode', 'node_modules', 'venv', 
    '.venv', 'env', 'virtualenv', 'dist', 'build',
    '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo',
    '.coverage', '.tox', '.nox', 'htmlcov',
    'eggs', '.eggs', '*.egg-info', '.installed.cfg',
    'develop-eggs', 'downloads', 'lib', 'lib64',
    'parts', 'sdist', 'var', 'wheels', '.Python',
    '.gitignore', '.gitattributes', '.gitmodules',
    '.svn', '.hg', '*.swp', '*.swo', '*~',
    '.cache', '.nyc_output', 'npm-debug.log*',
    'yarn-debug.log*', 'yarn-error.log*', '.npm',
    '.yarn-integrity', 'ENV', 'env.bak', 'venv.bak',
    'target', 'out', 'bin', 'obj', '._*',
    '.Spotlight-V100', '.Trashes', 'ehthumbs.db',
    'Desktop.ini', '*.log', 'logs', '*.tmp', '*.temp',
    '.tmp', '.temp', '_build', 'site', '.jekyll-cache',
    'Pipfile.lock', 'poetry.lock', 'package-lock.json',
    'yarn.lock'
]


def should_exclude(name: str, exclusions: List[str]) -> bool:
    """Check if a file or directory should be excluded."""
    # Direct name match
    if name in exclusions:
        return True
    
    # Pattern matching for wildcards
    for pattern in exclusions:
        if '*' in pattern:
            if pattern.startswith('*') and name.endswith(pattern[1:]):
                return True
            elif pattern.endswith('*') and name.startswith(pattern[:-1]):
                return True
    
    return False


def generate_tree_recursive(path: str, prefix: str = "", exclusions: List[str] = None, 
                          is_last: bool = True, max_depth: int = None, current_depth: int = 0) -> List[str]:
    """Recursively generate tree structure."""
    if exclusions is None:
        exclusions = DEFAULT_EXCLUSIONS
    
    if max_depth is not None and current_depth >= max_depth:
        return []
    
    lines = []
    
    try:
        # Get directory contents
        items = []
        if os.path.isdir(path):
            for item in os.listdir(path):
                if not should_exclude(item, exclusions):
                    item_path = os.path.join(path, item)
                    items.append((item, item_path, os.path.isdir(item_path)))
        
        # Sort items: directories first, then files, both alphabetically
        items.sort(key=lambda x: (not x[2], x[0].lower()))
        
        for i, (item_name, item_path, is_dir) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            
            # Choose the appropriate tree characters
            if is_last_item:
                current_prefix = "└── "
                next_prefix = prefix + "    "
            else:
                current_prefix = "├── "
                next_prefix = prefix + "│   "
            
            # Add current item
            lines.append(f"{prefix}{current_prefix}{item_name}")
            
            # Recursively process directories
            if is_dir:
                sub_lines = generate_tree_recursive(
                    item_path, 
                    next_prefix, 
                    exclusions, 
                    is_last_item,
                    max_depth,
                    current_depth + 1
                )
                lines.extend(sub_lines)
    
    except PermissionError:
        lines.append(f"{prefix}[Permission Denied]")
    except Exception as e:
        lines.append(f"{prefix}[Error: {str(e)}]")
    
    return lines


def generate_tree(root_path: str, exclusions: List[str] = None, max_depth: int = None) -> str:
    """Generate a complete tree structure for the given path."""
    if exclusions is None:
        exclusions = DEFAULT_EXCLUSIONS
    
    if not os.path.exists(root_path):
        return f"Error: Path '{root_path}' does not exist"
    
    # Get the base name for the root
    root_name = os.path.basename(os.path.abspath(root_path))
    if not root_name:  # Handle root directory case
        root_name = os.path.abspath(root_path)
    
    lines = [root_name]
    
    # Generate tree structure
    tree_lines = generate_tree_recursive(root_path, "", exclusions, True, max_depth)
    lines.extend(tree_lines)
    
    return '\n'.join(lines)


def clean_tree_content(content: str) -> str:
    """Clean up the tree content by removing empty lines and normalizing."""
    lines = content.split('\n')
    
    # Remove empty lines and strip whitespace
    cleaned_lines = []
    for line in lines:
        stripped = line.rstrip()
        if stripped:  # Only keep non-empty lines
            cleaned_lines.append(stripped)
    
    return '\n'.join(cleaned_lines)


def count_items(root_path: str, exclusions: List[str] = None) -> tuple:
    """Count files and directories in the tree."""
    if exclusions is None:
        exclusions = DEFAULT_EXCLUSIONS
    
    file_count = 0
    dir_count = 0
    
    for root, dirs, files in os.walk(root_path):
        # Filter directories
        dirs[:] = [d for d in dirs if not should_exclude(d, exclusions)]
        
        # Count directories
        dir_count += len(dirs)
        
        # Count files
        for file in files:
            if not should_exclude(file, exclusions):
                file_count += 1
    
    return file_count, dir_count


def main():
    parser = argparse.ArgumentParser(description="Generate directory tree structure")
    parser.add_argument("--root", required=True, help="Root directory to analyze")
    parser.add_argument("--output", required=True, help="Output directory for generated files")
    parser.add_argument("--max-depth", type=int, help="Maximum depth to traverse")
    parser.add_argument("--include-stats", action="store_true", help="Include file/directory statistics")
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.root):
        print(f"Error: Root directory '{args.root}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory
    try:
        os.makedirs(args.output, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate tree structure
    try:
        tree_content = generate_tree(args.root, DEFAULT_EXCLUSIONS, args.max_depth)
        tree_content = clean_tree_content(tree_content)
        
        # Add statistics if requested
        if args.include_stats:
            file_count, dir_count = count_items(args.root, DEFAULT_EXCLUSIONS)
            stats = f"\n\nStatistics:\n- Files: {file_count}\n- Directories: {dir_count}\n- Total items: {file_count + dir_count}"
            tree_content += stats
        
        # Write tree structure file
        tree_path = os.path.join(args.output, "tree-structure.txt")
        with open(tree_path, "w", encoding="utf-8") as f:
            f.write(tree_content)
        
        print(f"Tree structure saved to: {tree_path}")
        
        # Print summary
        file_count, dir_count = count_items(args.root, DEFAULT_EXCLUSIONS)
        print(f"Processed {dir_count} directories and {file_count} files")
        
    except Exception as e:
        print(f"Error generating tree structure: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 