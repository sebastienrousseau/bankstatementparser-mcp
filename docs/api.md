# API reference

The server's importable Python surface: the tools, the resource and the
prompt are plain functions, so an agent framework or a test can call
them in-process. Generated from the docstrings by mkdocstrings.

::: bankstatementparser_mcp.server
    options:
      members:
        - list_supported_formats
        - detect_format
        - parse_statement
        - validate_statement
        - summarize_statement
        - formats_resource
        - analyze_statement
        - main

::: bankstatementparser_mcp.adapters
    options:
      members:
        - as_langchain_tools
        - as_crewai_tools
        - as_llamaindex_tools

::: bankstatementparser_mcp.completion
