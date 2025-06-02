#!/usr/bin/env python3
"""
Generate module-level function documentation from Python code using AST parsing.
Adapted for MCP tool server usage.
"""

import os
import ast
import argparse
import sys
from typing import Dict, List, Optional, Any


class FunctionVisitor(ast.NodeVisitor):
    """AST visitor to extract module-level function information."""
    
    def __init__(self):
        self.functions = []
        self.imports = set()
        self.current_class = None
        self.current_function_depth = 0
        
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
        # Track when we're inside a class to skip class methods
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        # Only process module-level functions (not class methods or nested functions)
        if self.current_class is None and self.current_function_depth == 0:
            function_info = self._extract_function_info(node)
            self.functions.append(function_info)
        
        # Track nested function depth
        self.current_function_depth += 1
        self.generic_visit(node)
        self.current_function_depth -= 1
    
    def visit_AsyncFunctionDef(self, node):
        # Handle async functions the same way
        if self.current_class is None and self.current_function_depth == 0:
            function_info = self._extract_function_info(node, is_async=True)
            self.functions.append(function_info)
        
        self.current_function_depth += 1
        self.generic_visit(node)
        self.current_function_depth -= 1
    
    def _extract_function_info(self, node, is_async=False):
        """Extract detailed information about a function."""
        function_info = {
            'name': node.name,
            'is_async': is_async,
            'args': [],
            'defaults': [],
            'vararg': None,
            'kwarg': None,
            'returns': None,
            'decorators': [],
            'docstring': ast.get_docstring(node),
            'lineno': node.lineno,
            'is_private': node.name.startswith('_'),
            'type_hints': {}
        }
        
        # Extract arguments
        args = node.args
        
        # Regular arguments
        for i, arg in enumerate(args.args):
            arg_info = {
                'name': arg.arg,
                'annotation': self._get_annotation(arg.annotation),
                'default': None
            }
            
            # Check if this argument has a default value
            default_offset = len(args.args) - len(args.defaults)
            if i >= default_offset:
                default_index = i - default_offset
                arg_info['default'] = self._get_default_value(args.defaults[default_index])
            
            function_info['args'].append(arg_info)
        
        # Positional-only arguments (Python 3.8+)
        if hasattr(args, 'posonlyargs'):
            for arg in args.posonlyargs:
                arg_info = {
                    'name': arg.arg,
                    'annotation': self._get_annotation(arg.annotation),
                    'default': None,
                    'positional_only': True
                }
                function_info['args'].append(arg_info)
        
        # Keyword-only arguments
        for i, arg in enumerate(args.kwonlyargs):
            arg_info = {
                'name': arg.arg,
                'annotation': self._get_annotation(arg.annotation),
                'default': None,
                'keyword_only': True
            }
            
            # Check for default value
            if i < len(args.kw_defaults) and args.kw_defaults[i] is not None:
                arg_info['default'] = self._get_default_value(args.kw_defaults[i])
            
            function_info['args'].append(arg_info)
        
        # Variable arguments (*args)
        if args.vararg:
            function_info['vararg'] = {
                'name': args.vararg.arg,
                'annotation': self._get_annotation(args.vararg.annotation)
            }
        
        # Keyword arguments (**kwargs)
        if args.kwarg:
            function_info['kwarg'] = {
                'name': args.kwarg.arg,
                'annotation': self._get_annotation(args.kwarg.annotation)
            }
        
        # Return type annotation
        if node.returns:
            function_info['returns'] = self._get_annotation(node.returns)
        
        # Extract decorators
        for decorator in node.decorator_list:
            decorator_name = self._get_decorator_name(decorator)
            if decorator_name:
                function_info['decorators'].append(decorator_name)
        
        return function_info
    
    def _get_annotation(self, annotation):
        """Extract type annotation as string."""
        if annotation is None:
            return None
        
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return self._get_attribute_name(annotation)
        elif isinstance(annotation, ast.Constant):
            return repr(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            return self._get_subscript_name(annotation)
        else:
            # For complex annotations, try to unparse if available
            try:
                if hasattr(ast, 'unparse'):  # Python 3.9+
                    return ast.unparse(annotation)
                else:
                    return str(annotation)
            except:
                return str(type(annotation).__name__)
    
    def _get_attribute_name(self, node):
        """Extract full attribute name from ast.Attribute node."""
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}.{node.attr}"
            elif isinstance(node.value, ast.Attribute):
                parent = self._get_attribute_name(node.value)
                return f"{parent}.{node.attr}" if parent else node.attr
        return None
    
    def _get_subscript_name(self, node):
        """Extract subscript type like List[str] or Dict[str, int]."""
        if isinstance(node, ast.Subscript):
            value_name = self._get_annotation(node.value)
            slice_name = self._get_annotation(node.slice)
            if value_name and slice_name:
                return f"{value_name}[{slice_name}]"
            elif value_name:
                return value_name
        return None
    
    def _get_default_value(self, node):
        """Extract default value as string."""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_name(node)
        elif isinstance(node, ast.List):
            return "[]"
        elif isinstance(node, ast.Dict):
            return "{}"
        elif isinstance(node, ast.Tuple):
            return "()"
        else:
            try:
                if hasattr(ast, 'unparse'):  # Python 3.9+
                    return ast.unparse(node)
                else:
                    return "..."
            except:
                return "..."
    
    def _get_decorator_name(self, decorator):
        """Extract decorator name."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return self._get_attribute_name(decorator)
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return f"{decorator.func.id}(...)"
            elif isinstance(decorator.func, ast.Attribute):
                func_name = self._get_attribute_name(decorator.func)
                return f"{func_name}(...)" if func_name else None
        return None


def parse_python_file(file_path: str) -> FunctionVisitor:
    """Parse a Python file and extract function information."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        visitor = FunctionVisitor()
        visitor.visit(tree)
        return visitor
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return FunctionVisitor()


def parse_directory(root_path: str) -> Dict[str, List[Dict]]:
    """Parse all Python files in a directory and return function information by module."""
    modules = {}
    
    for root, dirs, files in os.walk(root_path):
        # Skip common exclusion patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
            '__pycache__', 'venv', '.venv', 'env', 'virtualenv', 'node_modules'
        ]]
        
        python_files = [f for f in files if f.endswith('.py') and not f.startswith('.')]
        
        for py_file in python_files:
            file_path = os.path.join(root, py_file)
            
            # Determine module name
            rel_path = os.path.relpath(file_path, root_path)
            module_name = rel_path.replace(os.sep, '.').replace('.py', '')
            
            # Parse file
            visitor = parse_python_file(file_path)
            
            if visitor.functions:  # Only include modules with functions
                modules[module_name] = {
                    'file_path': rel_path,
                    'functions': visitor.functions,
                    'imports': list(visitor.imports)
                }
    
    return modules


def format_function_signature(func_info: Dict) -> str:
    """Format a function signature string."""
    parts = []
    
    # Add async keyword
    if func_info['is_async']:
        parts.append('async')
    
    parts.append('def')
    parts.append(func_info['name'])
    
    # Build parameter list
    params = []
    
    for arg in func_info['args']:
        param_str = arg['name']
        
        # Add type annotation
        if arg['annotation']:
            param_str += f": {arg['annotation']}"
        
        # Add default value
        if arg['default'] is not None:
            param_str += f" = {arg['default']}"
        
        params.append(param_str)
    
    # Add *args
    if func_info['vararg']:
        vararg_str = f"*{func_info['vararg']['name']}"
        if func_info['vararg']['annotation']:
            vararg_str += f": {func_info['vararg']['annotation']}"
        params.append(vararg_str)
    
    # Add **kwargs
    if func_info['kwarg']:
        kwarg_str = f"**{func_info['kwarg']['name']}"
        if func_info['kwarg']['annotation']:
            kwarg_str += f": {func_info['kwarg']['annotation']}"
        params.append(kwarg_str)
    
    signature = f"{' '.join(parts)}({', '.join(params)})"
    
    # Add return type
    if func_info['returns']:
        signature += f" -> {func_info['returns']}"
    
    return signature


def generate_documentation(modules: Dict[str, Dict]) -> str:
    """Generate formatted documentation from parsed modules."""
    lines = ['# Module Functions Documentation', '']
    
    if not modules:
        lines.append('No module-level functions found.')
        return '\n'.join(lines)
    
    # Sort modules by name
    sorted_modules = sorted(modules.items())
    
    for module_name, module_info in sorted_modules:
        lines.append(f'## Module: {module_name}')
        lines.append(f'**File:** `{module_info["file_path"]}`')
        lines.append('')
        
        # Add imports if any
        if module_info['imports']:
            lines.append('**Imports:**')
            for imp in sorted(module_info['imports']):
                lines.append(f'- {imp}')
            lines.append('')
        
        # Add functions
        lines.append('**Functions:**')
        lines.append('')
        
        # Sort functions by line number
        sorted_functions = sorted(module_info['functions'], key=lambda f: f['lineno'])
        
        for func in sorted_functions:
            # Function signature
            signature = format_function_signature(func)
            lines.append(f'### `{signature}`')
            lines.append('')
            
            # Add decorators
            if func['decorators']:
                lines.append('**Decorators:**')
                for decorator in func['decorators']:
                    lines.append(f'- `@{decorator}`')
                lines.append('')
            
            # Add docstring
            if func['docstring']:
                lines.append('**Description:**')
                # Clean up docstring
                docstring_lines = func['docstring'].strip().split('\n')
                for doc_line in docstring_lines:
                    lines.append(f'{doc_line.strip()}')
                lines.append('')
            
            # Add line number
            lines.append(f'**Line:** {func["lineno"]}')
            lines.append('')
            lines.append('---')
            lines.append('')
        
        lines.append('')
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate module function documentation from Python code")
    parser.add_argument("--root", required=True, help="Root directory to analyze")
    parser.add_argument("--output", required=True, help="Output directory for generated files")
    
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
    
    # Parse directory and generate documentation
    try:
        modules = parse_directory(args.root)
        
        if not modules:
            print("No module-level functions found in the specified directory", file=sys.stderr)
            # Still create the file with a message
            documentation = "# Module Functions Documentation\n\nNo module-level functions found."
        else:
            documentation = generate_documentation(modules)
        
        # Write documentation file
        doc_path = os.path.join(args.output, "module-functions.txt")
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(documentation)
        
        print(f"Module functions documentation saved to: {doc_path}")
        
        # Print summary
        total_functions = sum(len(mod['functions']) for mod in modules.values())
        print(f"Processed {len(modules)} modules with {total_functions} functions")
        
    except Exception as e:
        print(f"Error generating module functions documentation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 