# MCP Docs Tools Architecture

## Overview

The MCP Docs Tools is a hybrid Node.js/Python system that provides documentation generation capabilities through the Model Context Protocol (MCP). The architecture is designed for reliability, performance, and ease of maintenance.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Client (AI Assistant)                │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP Protocol (stdio)
┌─────────────────────▼───────────────────────────────────────┐
│                  Node.js MCP Server                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Tool Registry                          │   │
│  │  • create_class_diagram                            │   │
│  │  • create_tree_structure                           │   │
│  │  • create_module_functions                         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Tool Wrappers                         │   │
│  │  • Parameter validation                            │   │
│  │  • Process spawning                                │   │
│  │  • Error handling                                  │   │
│  │  • Response formatting                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │ spawn() calls
┌─────────────────────▼───────────────────────────────────────┐
│                  Python Scripts                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              AST Parsers                           │   │
│  │  • generate_uml.py (Class analysis)               │   │
│  │  • generate_functions.py (Function analysis)      │   │
│  │  • generate_tree.py (Directory traversal)         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Output Generators                     │   │
│  │  • PlantUML syntax generation                      │   │
│  │  • Markdown documentation                          │   │
│  │  • Tree structure formatting                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │ File I/O
┌─────────────────────▼───────────────────────────────────────┐
│                  File System                               │
│  • docs/uml.txt                                           │
│  • docs/tree-structure.txt                                │
│  • docs/module-functions.txt                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Node.js MCP Server Layer

**Purpose**: Protocol handling and process orchestration

**Key Components**:
- `src/server.js`: Main MCP server implementation
- `src/tools/`: Individual tool wrappers
- `bin/server.js`: Entry point and CLI interface

**Responsibilities**:
- MCP protocol compliance
- Tool registration and discovery
- Parameter validation and sanitization
- Python process lifecycle management
- Error handling and response formatting
- Logging and debugging support

**Design Decisions**:
- **Stateless**: No persistent state between tool calls
- **Process Isolation**: Each tool execution spawns a separate Python process
- **Error Boundaries**: Comprehensive error handling at each layer
- **Async/Await**: Modern JavaScript patterns for process management

### 2. Python Analysis Layer

**Purpose**: Code analysis and documentation generation

**Key Components**:
- `python/generate_uml.py`: AST-based class analysis
- `python/generate_functions.py`: Function signature extraction
- `python/generate_tree.py`: Directory structure analysis

**Responsibilities**:
- Python AST parsing and traversal
- Type annotation extraction
- Decorator and metadata analysis
- Inheritance relationship mapping
- File system traversal with exclusions
- Output formatting and generation

**Design Decisions**:
- **AST-based**: Uses Python's built-in `ast` module for reliable parsing
- **Visitor Pattern**: Clean separation of concerns in AST traversal
- **CLI Interface**: Each script can be run independently for testing
- **No Dependencies**: Uses only Python standard library

### 3. Tool Interface Layer

**Purpose**: Bridge between MCP protocol and Python scripts

**Key Components**:
- `src/tools/class-diagram.js`
- `src/tools/tree-structure.js`
- `src/tools/module-functions.js`

**Responsibilities**:
- Parameter validation and transformation
- Python script execution and monitoring
- Output path management
- Error translation and formatting
- Success/failure reporting

## Data Flow

### 1. Tool Invocation Flow

```
MCP Client Request
    ↓
Parameter Validation
    ↓
Python Script Spawn
    ↓
File System Analysis
    ↓
Documentation Generation
    ↓
File Output
    ↓
Response Formatting
    ↓
MCP Client Response
```

### 2. Error Handling Flow

```
Error Occurrence
    ↓
Error Capture (Python/Node.js)
    ↓
Error Classification
    ↓
User-Friendly Message Generation
    ↓
MCP Error Response
    ↓
Client Error Display
```

## Key Design Patterns

### 1. Hybrid Architecture Pattern

**Problem**: Need reliable Python AST parsing with MCP protocol support
**Solution**: Node.js for protocol + Python for analysis
**Benefits**:
- Leverages Python's superior AST capabilities
- Maintains Node.js ecosystem compatibility
- Clean separation of concerns
- Independent testing of components

### 2. Process Isolation Pattern

**Problem**: Ensure tool reliability and prevent memory leaks
**Solution**: Spawn separate Python processes for each tool execution
**Benefits**:
- Memory isolation between tool calls
- Crash isolation (one tool failure doesn't affect others)
- Simplified state management
- Easy debugging and profiling

### 3. Visitor Pattern (Python AST)

**Problem**: Need to traverse complex AST structures efficiently
**Solution**: Implement custom NodeVisitor classes
**Benefits**:
- Clean separation of parsing logic
- Extensible for new node types
- Follows Python AST best practices
- Easy to test and maintain

### 4. Command Pattern (Tool Interface)

**Problem**: Need consistent interface for different tool types
**Solution**: Standardized tool wrapper pattern
**Benefits**:
- Consistent error handling
- Uniform parameter validation
- Easy to add new tools
- Simplified testing

## Performance Considerations

### 1. Process Spawning Overhead

**Challenge**: Python process startup time
**Mitigation**:
- Lightweight Python scripts with minimal imports
- No external dependencies to reduce startup time
- Efficient argument parsing

**Metrics**:
- Cold start: ~100-200ms
- Warm execution: ~50-100ms for small projects

### 2. Memory Usage

**Challenge**: Large project analysis memory requirements
**Mitigation**:
- Streaming file processing where possible
- Smart exclusions to reduce file count
- Process isolation prevents memory accumulation

**Metrics**:
- Node.js baseline: ~10-20 MB
- Python process: ~5-15 MB per execution
- Linear scaling with project size

### 3. File I/O Optimization

**Challenge**: Efficient file system traversal
**Mitigation**:
- Intelligent exclusion patterns
- Single-pass directory traversal
- Minimal file content reading (only when needed)

## Security Considerations

### 1. Path Validation

**Risk**: Directory traversal attacks
**Mitigation**:
- Path sanitization and validation
- Restricted to specified project directories
- No symbolic link following

### 2. Process Execution

**Risk**: Command injection through parameters
**Mitigation**:
- Parameterized process spawning
- Input validation and sanitization
- No shell execution

### 3. File System Access

**Risk**: Unauthorized file access
**Mitigation**:
- Read-only access to source files
- Write access only to designated docs directory
- Respect file system permissions

## Extensibility

### Adding New Tools

1. **Create Python Script**: Implement analysis logic
2. **Add Tool Wrapper**: Create Node.js wrapper in `src/tools/`
3. **Register Tool**: Add to server tool registry
4. **Add Documentation**: Update API docs and examples

### Extending Existing Tools

1. **Modify Python Script**: Add new analysis capabilities
2. **Update Output Format**: Enhance documentation generation
3. **Maintain Backward Compatibility**: Ensure existing outputs still work
4. **Add Tests**: Verify new functionality

## Testing Strategy

### 1. Unit Testing

**Python Scripts**:
- AST parsing logic
- Output formatting
- Error handling

**Node.js Components**:
- Parameter validation
- Process management
- Error handling

### 2. Integration Testing

**End-to-End**:
- Full tool execution workflows
- Error scenarios
- Performance benchmarks

**Cross-Platform**:
- Windows, macOS, Linux compatibility
- Different Python versions
- Various project structures

### 3. Performance Testing

**Scalability**:
- Large project handling
- Memory usage profiling
- Execution time benchmarks

## Deployment Considerations

### 1. Dependencies

**Node.js**:
- Minimal dependencies (MCP SDK, Zod)
- No native modules for cross-platform compatibility

**Python**:
- Standard library only
- No external package requirements

### 2. Distribution

**NPM Package**:
- Self-contained with Python scripts
- Cross-platform compatibility
- Easy installation and updates

### 3. Runtime Requirements

**System Requirements**:
- Node.js ≥18.0.0
- Python 3.x
- File system read/write permissions

## Future Enhancements

### 1. Performance Optimizations

- Python process pooling for repeated calls
- Incremental analysis for large projects
- Caching mechanisms for unchanged files

### 2. Feature Extensions

- Support for additional languages (JavaScript, TypeScript)
- Interactive documentation generation
- Integration with documentation platforms

### 3. Developer Experience

- Configuration file support
- Custom exclusion patterns
- Verbose logging and debugging modes 