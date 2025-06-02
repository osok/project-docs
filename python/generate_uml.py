#!/usr/bin/env python3
"""
Generate UML class diagrams from Python code using AST parsing.
Adapted for MCP tool server usage.
"""

import os
import ast
import argparse
import sys
from collections import Counter
from typing import Dict, List, Set, Optional, Tuple


class UMLClassVisitor(ast.NodeVisitor):
    """AST visitor to extract class information for UML diagrams."""
    
    def __init__(self):
        self.classes = {}
        self.current_class = None
        self.imports = set()
        self.inheritance_relationships = []
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        class_name = node.name
        self.current_class = class_name
        
        # Initialize class info
        self.classes[class_name] = {
            'methods': [],
            'attributes': [],
            'bases': [],
            'decorators': [],
            'docstring': ast.get_docstring(node)
        }
        
        # Extract base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.classes[class_name]['bases'].append(base.id)
                self.inheritance_relationships.append((class_name, base.id))
            elif isinstance(base, ast.Attribute):
                base_name = self._get_attribute_name(base)
                if base_name:
                    self.classes[class_name]['bases'].append(base_name)
                    self.inheritance_relationships.append((class_name, base_name))
        
        # Extract decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                self.classes[class_name]['decorators'].append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorator_name = self._get_attribute_name(decorator)
                if decorator_name:
                    self.classes[class_name]['decorators'].append(decorator_name)
        
        # Visit class body
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        if self.current_class:
            method_info = {
                'name': node.name,
                'args': [],
                'returns': None,
                'decorators': [],
                'is_private': node.name.startswith('_'),
                'is_static': False,
                'is_class_method': False,
                'docstring': ast.get_docstring(node)
            }
            
            # Extract arguments
            for arg in node.args.args:
                method_info['args'].append(arg.arg)
            
            # Extract return annotation
            if node.returns:
                if isinstance(node.returns, ast.Name):
                    method_info['returns'] = node.returns.id
                elif isinstance(node.returns, ast.Attribute):
                    method_info['returns'] = self._get_attribute_name(node.returns)
            
            # Extract decorators
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    decorator_name = decorator.id
                    method_info['decorators'].append(decorator_name)
                    if decorator_name == 'staticmethod':
                        method_info['is_static'] = True
                    elif decorator_name == 'classmethod':
                        method_info['is_class_method'] = True
                elif isinstance(decorator, ast.Attribute):
                    decorator_name = self._get_attribute_name(decorator)
                    if decorator_name:
                        method_info['decorators'].append(decorator_name)
            
            self.classes[self.current_class]['methods'].append(method_info)
        
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        if self.current_class:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    attr_name = target.id
                    if not attr_name.startswith('_'):  # Only public attributes
                        attr_info = {
                            'name': attr_name,
                            'type': None,
                            'is_private': attr_name.startswith('_')
                        }
                        
                        # Try to infer type from value
                        if isinstance(node.value, ast.Constant):
                            attr_info['type'] = type(node.value.value).__name__
                        elif isinstance(node.value, ast.Name):
                            attr_info['type'] = node.value.id
                        
                        self.classes[self.current_class]['attributes'].append(attr_info)
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node):
        """Handle annotated assignments (type hints)."""
        if self.current_class and isinstance(node.target, ast.Name):
            attr_name = node.target.id
            attr_info = {
                'name': attr_name,
                'type': None,
                'is_private': attr_name.startswith('_')
            }
            
            # Extract type annotation
            if isinstance(node.annotation, ast.Name):
                attr_info['type'] = node.annotation.id
            elif isinstance(node.annotation, ast.Attribute):
                attr_info['type'] = self._get_attribute_name(node.annotation)
            
            self.classes[self.current_class]['attributes'].append(attr_info)
        
        self.generic_visit(node)
    
    def _get_attribute_name(self, node):
        """Extract full attribute name from ast.Attribute node."""
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}.{node.attr}"
            elif isinstance(node.value, ast.Attribute):
                parent = self._get_attribute_name(node.value)
                return f"{parent}.{node.attr}" if parent else node.attr
        return None


def parse_python_file(file_path: str) -> UMLClassVisitor:
    """Parse a Python file and extract class information."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        visitor = UMLClassVisitor()
        visitor.visit(tree)
        return visitor
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return UMLClassVisitor()


def parse_directory(root_path: str) -> Dict[str, UMLClassVisitor]:
    """Parse all Python files in a directory and return class information by package."""
    packages = {}
    
    for root, dirs, files in os.walk(root_path):
        # Skip common exclusion patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
            '__pycache__', 'venv', '.venv', 'env', 'virtualenv', 'node_modules'
        ]]
        
        python_files = [f for f in files if f.endswith('.py') and not f.startswith('.')]
        
        if python_files:
            # Determine package name
            rel_path = os.path.relpath(root, root_path)
            if rel_path == '.':
                package_name = 'root'
            else:
                package_name = rel_path.replace(os.sep, '.')
            
            # Initialize package visitor
            if package_name not in packages:
                packages[package_name] = UMLClassVisitor()
            
            # Parse each Python file
            for py_file in python_files:
                file_path = os.path.join(root, py_file)
                visitor = parse_python_file(file_path)
                
                # Merge visitor results into package visitor
                packages[package_name].classes.update(visitor.classes)
                packages[package_name].imports.update(visitor.imports)
                packages[package_name].inheritance_relationships.extend(visitor.inheritance_relationships)
    
    return packages


def generate_plantuml(packages: Dict[str, UMLClassVisitor]) -> str:
    """Generate PlantUML syntax from parsed class information."""
    uml_lines = ['@startuml', '']
    
    # Add styling
    uml_lines.extend([
        '!theme plain',
        'skinparam classAttributeIconSize 0',
        'skinparam classFontStyle bold',
        'skinparam packageStyle rectangle',
        ''
    ])
    
    # Generate classes by package
    for package_name, visitor in packages.items():
        if not visitor.classes:
            continue
        
        if package_name != 'root':
            uml_lines.append(f'package "{package_name}" {{')
        
        for class_name, class_info in visitor.classes.items():
            uml_lines.append(f'  class {class_name} {{')
            
            # Add attributes
            for attr in class_info['attributes']:
                visibility = '-' if attr['is_private'] else '+'
                type_info = f": {attr['type']}" if attr['type'] else ''
                uml_lines.append(f'    {visibility}{attr["name"]}{type_info}')
            
            if class_info['attributes'] and class_info['methods']:
                uml_lines.append('    --')
            
            # Add methods
            for method in class_info['methods']:
                visibility = '-' if method['is_private'] else '+'
                args_str = ', '.join(method['args'][1:])  # Skip 'self'
                return_str = f": {method['returns']}" if method['returns'] else ''
                
                # Add method modifiers
                modifiers = []
                if method['is_static']:
                    modifiers.append('{static}')
                if method['is_class_method']:
                    modifiers.append('{class}')
                
                modifier_str = ' '.join(modifiers)
                if modifier_str:
                    modifier_str = f'{modifier_str} '
                
                uml_lines.append(f'    {visibility}{modifier_str}{method["name"]}({args_str}){return_str}')
            
            uml_lines.append('  }')
            uml_lines.append('')
        
        if package_name != 'root':
            uml_lines.append('}')
            uml_lines.append('')
    
    # Add inheritance relationships
    all_relationships = []
    for visitor in packages.values():
        all_relationships.extend(visitor.inheritance_relationships)
    
    if all_relationships:
        uml_lines.append('/' + '* Inheritance relationships *' + '/')
        for child, parent in all_relationships:
            uml_lines.append(f'{parent} <|-- {child}')
    
    uml_lines.append('')
    uml_lines.append('@enduml')
    
    return '\n'.join(uml_lines)


def main():
    parser = argparse.ArgumentParser(description="Generate UML class diagrams from Python code")
    parser.add_argument("--root", required=True, help="Root directory to analyze")
    parser.add_argument("--output", required=True, help="Output directory for generated files")
    parser.add_argument("--uml-only", action="store_true", help="Generate only UML diagram")
    
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
    
    # Parse directory and generate UML
    try:
        packages = parse_directory(args.root)
        
        if not any(pkg.classes for pkg in packages.values()):
            print("No Python classes found in the specified directory", file=sys.stderr)
            sys.exit(1)
        
        uml_source = generate_plantuml(packages)
        
        # Write UML file
        uml_path = os.path.join(args.output, "uml.txt")
        with open(uml_path, "w", encoding="utf-8") as f:
            f.write(uml_source)
        
        print(f"UML diagram saved to: {uml_path}")
        
        # Print summary
        total_classes = sum(len(pkg.classes) for pkg in packages.values())
        print(f"Processed {len(packages)} packages with {total_classes} classes")
        
    except Exception as e:
        print(f"Error generating UML diagram: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 