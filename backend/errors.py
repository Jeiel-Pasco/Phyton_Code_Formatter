"""Centralized Error Handling Module for Code Formatter.

Provides structured exception classes and serialization for lexical, syntax,
and pipeline errors across supported languages.
"""

from typing import Optional, Dict, Any


class FormatterException(Exception):
    """Base exception for all code formatter errors."""

    def __init__(
        self,
        message: str,
        error_type: str = "FormatterError",
        line: Optional[int] = None,
        column: Optional[int] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.line = line
        self.column = column
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a structured dictionary for JSON responses."""
        result: Dict[str, Any] = {
            "type": self.error_type,
            "message": self.message,
        }
        if self.line is not None:
            result["line"] = self.line
        if self.column is not None:
            result["column"] = self.column
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result

    def format_user_message(self) -> str:
        """Format an informative user-facing error message matching UI specifications."""
        location = ""
        if self.line is not None and self.column is not None:
            location = f" at line {self.line}, column {self.column}"
        elif self.line is not None:
            location = f" at line {self.line}"

        base = f"{self.error_type}{location}: {self.message}"
        if self.suggestion:
            base += f" {self.suggestion}"
        return base


class LexerError(FormatterException):
    """Raised when the lexical analyzer encounters an invalid or unterminated token."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_type="Lexical error",
            line=line,
            column=column,
            suggestion=suggestion or "Fix the invalid token and format again."
        )


class SyntaxError(FormatterException):
    """Raised when the parser encounters a structural or grammatical syntax error."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_type="Syntax error",
            line=line,
            column=column,
            suggestion=suggestion or "Fix the source and format again."
        )


class UnsupportedLanguageError(FormatterException):
    """Raised when an unrecognized programming language is specified."""

    def __init__(self, language: str):
        super().__init__(
            message=f"Language '{language}' is not supported.",
            error_type="Unsupported language",
            suggestion="Supported languages are: python, javascript, java, c, cpp."
        )


class FormattingError(FormatterException):
    """Raised when an internal error occurs during AST formatting / code generation."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_type="Formatting error",
            line=line,
            column=column,
            suggestion=suggestion
        )
