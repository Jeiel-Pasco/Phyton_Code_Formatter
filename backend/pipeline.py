"""Formatting Pipeline Controller for Code Formatter.

Coordinates lexical analysis, parsing, and code printing.
Collects execution statistics and provides consistent error reporting.
"""

import time
from typing import Dict, Any, Optional
from backend.lexer import tokenize, TokenType
from backend.parser import parse, ProgramNode, CommentNode, ASTNode
from backend.printer import format_ast
from backend.errors import (
    FormatterException, UnsupportedLanguageError, LexerError, SyntaxError, FormattingError
)

SUPPORTED_LANGUAGES = {
    "c": {"name": "C", "ext": ".c", "sample_name": "main.c"},
    "cpp": {"name": "C++", "ext": ".cpp", "sample_name": "main.cpp"},
    "c++": {"name": "C++", "ext": ".cpp", "sample_name": "main.cpp"},
    "java": {"name": "Java", "ext": ".java", "sample_name": "Main.java"},
    "javascript": {"name": "JavaScript", "ext": ".js", "sample_name": "index.js"},
    "js": {"name": "JavaScript", "ext": ".js", "sample_name": "index.js"},
    "python": {"name": "Python", "ext": ".py", "sample_name": "script.py"},
    "py": {"name": "Python", "ext": ".py", "sample_name": "script.py"},
}


def _count_comments(node: ASTNode) -> int:
    """Recursively count comment nodes in the AST."""
    count = 0
    if isinstance(node, CommentNode):
        count += 1

    # Check child nodes / statements
    if hasattr(node, "body"):
        body = node.body
        if isinstance(body, list):
            for child in body:
                count += _count_comments(child)
        elif isinstance(body, ASTNode):
            count += _count_comments(body)

    if hasattr(node, "statements"):
        for stmt in getattr(node, "statements", []):
            count += _count_comments(stmt)

    if hasattr(node, "then_branch") and node.then_branch:
        count += _count_comments(node.then_branch)
    if hasattr(node, "else_branch") and node.else_branch:
        count += _count_comments(node.else_branch)

    return count


def format_code(
    code: str,
    language: str = "c",
    indent_size: int = 4,
    indent_style: str = "spaces",
    max_line_length: int = 80
) -> Dict[str, Any]:
    """Execute the full code formatting pipeline.

    Args:
        code: Unformatted source code string.
        language: Target programming language (python, javascript, java, c, cpp).
        indent_size: Number of spaces or tabs per indentation level.
        indent_style: 'spaces' or 'tabs'.
        max_line_length: Target column width.

    Returns:
        Structured dictionary with success flag, formatted code, and metrics.
    """
    start_time = time.perf_counter()
    lang_key = language.strip().lower()

    if lang_key not in SUPPORTED_LANGUAGES:
        err = UnsupportedLanguageError(language)
        return {
            "success": False,
            "error": err.to_dict(),
            "user_message": err.format_user_message(),
            "formatted_code": "",
            "language": language,
            "execution_time_ms": 0.0,
        }

    # Empty code handling
    if not code or not code.strip():
        return {
            "success": True,
            "formatted_code": "",
            "language": lang_key,
            "execution_time_ms": 0.05,
            "original_lines": 0,
            "formatted_lines": 0,
            "comments_preserved": 0,
            "lexer_status": "OK",
            "parser_status": "OK",
            "indent_size": indent_size,
            "indent_style": indent_style,
            "max_line": max_line_length,
        }

    original_lines = len(code.splitlines())

    try:
        # Step 1: Lexical Analysis
        tokens = tokenize(code, lang_key)
        lexer_status = "OK"

        # Step 2: Syntax Parsing
        ast = parse(tokens, lang_key)
        parser_status = "OK"
        comments_preserved = _count_comments(ast)

        # Step 3: Code Generation / Pretty Printing
        formatted_code = format_ast(
            ast,
            language=lang_key,
            indent_size=indent_size,
            indent_style=indent_style,
            max_line_length=max_line_length
        )

        end_time = time.perf_counter()
        exec_ms = round((end_time - start_time) * 1000, 2)
        formatted_lines = len(formatted_code.splitlines())

        return {
            "success": True,
            "formatted_code": formatted_code,
            "language": lang_key,
            "execution_time_ms": max(exec_ms, 0.01),
            "original_lines": original_lines,
            "formatted_lines": formatted_lines,
            "comments_preserved": comments_preserved,
            "lexer_status": lexer_status,
            "parser_status": parser_status,
            "indent_size": indent_size,
            "indent_style": indent_style,
            "max_line": max_line_length,
        }

    except FormatterException as fe:
        end_time = time.perf_counter()
        exec_ms = round((end_time - start_time) * 1000, 2)
        return {
            "success": False,
            "error": fe.to_dict(),
            "user_message": fe.format_user_message(),
            "formatted_code": "",
            "language": lang_key,
            "execution_time_ms": exec_ms,
            "original_lines": original_lines,
            "formatted_lines": 0,
        }
    except Exception as exc:
        end_time = time.perf_counter()
        exec_ms = round((end_time - start_time) * 1000, 2)
        internal_err = FormattingError(
            message=f"Internal formatting error: {str(exc)}",
            suggestion="Verify code syntax and input structure."
        )
        return {
            "success": False,
            "error": internal_err.to_dict(),
            "user_message": internal_err.format_user_message(),
            "formatted_code": "",
            "language": lang_key,
            "execution_time_ms": exec_ms,
            "original_lines": original_lines,
            "formatted_lines": 0,
        }
