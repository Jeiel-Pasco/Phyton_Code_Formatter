"""Lexical Analyzer (Lexer) for Multi-Language Code Formatter.

Tokenizes source code into a structured sequence of tokens with line/column tracking,
language-specific keyword recognition, comment preservation, and strict error checking.
"""

from enum import Enum, auto
from typing import List, Optional, Set
from backend.errors import LexerError


class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    OPERATOR = auto()
    DELIMITER = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMENT = auto()
    NEWLINE = auto()
    PREPROCESSOR = auto()
    EOF = auto()


class Token:
    """Represents a lexical token with position metadata."""

    def __init__(
        self,
        type_: TokenType,
        value: str,
        line: int,
        column: int,
        end_line: Optional[int] = None,
        end_column: Optional[int] = None
    ):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
        self.end_line = end_line if end_line is not None else line
        self.end_column = end_column if end_column is not None else (column + len(value))

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"

    def to_dict(self):
        return {
            "type": self.type.name,
            "value": self.value,
            "line": self.line,
            "column": self.column,
        }


# Language-specific keyword dictionaries
C_KEYWORDS: Set[str] = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "int", "long", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "unsigned", "void", "volatile",
    "while", "size_t", "bool", "true", "false", "NULL", "string"
}

CPP_KEYWORDS: Set[str] = C_KEYWORDS | {
    "alignas", "alignof", "and", "and_eq", "asm", "atomic_cancel", "atomic_commit",
    "atomic_noexcept", "bitand", "bitor", "catch", "char16_t", "char32_t",
    "class", "compl", "concept", "consteval", "constexpr", "constinit", "const_cast",
    "co_await", "co_return", "co_yield", "decltype", "delete", "dynamic_cast",
    "explicit", "export", "friend", "inline", "mutable", "namespace", "new",
    "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq",
    "private", "protected", "public", "reinterpret_cast", "requires", "static_assert",
    "static_cast", "template", "this", "thread_local", "throw", "try", "typeid",
    "typename", "using", "virtual", "wchar_t", "xor", "xor_eq", "std", "cout", "cin", "endl"
}

JAVA_KEYWORDS: Set[str] = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while", "true", "false", "null", "String"
}

JS_KEYWORDS: Set[str] = {
    "await", "break", "case", "catch", "class", "const", "continue", "debugger",
    "default", "delete", "do", "else", "export", "extends", "finally", "for",
    "function", "if", "import", "in", "instanceof", "new", "return", "super",
    "switch", "this", "throw", "try", "typeof", "var", "void", "while", "with",
    "yield", "let", "static", "enum", "true", "false", "null", "undefined",
    "NaN", "Infinity", "async", "of", "console"
}

PYTHON_KEYWORDS: Set[str] = {
    "False", "None", "True", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally",
    "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
    "print", "range", "len", "self"
}

LANGUAGE_KEYWORDS = {
    "c": C_KEYWORDS,
    "cpp": CPP_KEYWORDS,
    "c++": CPP_KEYWORDS,
    "java": JAVA_KEYWORDS,
    "javascript": JS_KEYWORDS,
    "js": JS_KEYWORDS,
    "python": PYTHON_KEYWORDS,
    "py": PYTHON_KEYWORDS,
}

MULTI_CHAR_OPS = [
    "===", "!==", "::", "->", "=>", "==", "!=", "<=", ">=", "&&", "||", "++", "--",
    "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>=",
    "<<", ">>", "**"
]

SINGLE_CHAR_OPS = set("+-*/%=<>!&|^~?")
DELIMITERS = set(";,.:")
PARENS = {"(": TokenType.LPAREN, ")": TokenType.RPAREN}
BRACES = {"{": TokenType.LBRACE, "}": TokenType.RBRACE}
BRACKETS = {"[": TokenType.LBRACKET, "]": TokenType.RBRACKET}


class Lexer:
    """Multi-language lexical analyzer."""

    def __init__(self, source: str, language: str = "javascript"):
        self.source = source
        self.language = language.lower()
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1
        self.keywords = LANGUAGE_KEYWORDS.get(self.language, JS_KEYWORDS)

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return ""

    def _advance(self) -> str:
        if self.pos >= self.length:
            return ""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self.source.startswith(expected, self.pos):
            for _ in expected:
                self._advance()
            return True
        return False

    def tokenize(self) -> List[Token]:
        """Convert the entire source code into a list of Tokens."""
        tokens: List[Token] = []

        while self.pos < self.length:
            ch = self._peek()

            # Skip or preserve whitespace
            if ch in " \t\r":
                self._advance()
                continue

            # Newlines
            if ch == "\n":
                line, col = self.line, self.column
                self._advance()
                # For Python, newlines are syntactically relevant
                if self.language in ("python", "py"):
                    tokens.append(Token(TokenType.NEWLINE, "\n", line, col))
                continue

            # Preprocessor directives (#include, #define for C/C++)
            if ch == "#" and self.language in ("c", "cpp", "c++"):
                tokens.append(self._lex_preprocessor())
                continue

            # Python comments (#)
            if ch == "#" and self.language in ("python", "py"):
                tokens.append(self._lex_python_comment())
                continue

            # C/C++/Java/JS Comments (// or /* ... */)
            if ch == "/" and self._peek(1) == "/":
                tokens.append(self._lex_line_comment())
                continue

            if ch == "/" and self._peek(1) == "*":
                tokens.append(self._lex_block_comment())
                continue

            # Numbers
            if ch.isdigit():
                tokens.append(self._lex_number())
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == "_" or (self.language in ("javascript", "js") and ch == "$"):
                tokens.append(self._lex_identifier_or_keyword())
                continue

            # String literals
            if ch in ('"', "'", "`"):
                tokens.append(self._lex_string())
                continue

            # Delimiters and brackets
            if ch in PARENS:
                line, col = self.line, self.column
                self._advance()
                tokens.append(Token(PARENS[ch], ch, line, col))
                continue

            if ch in BRACES:
                line, col = self.line, self.column
                self._advance()
                tokens.append(Token(BRACES[ch], ch, line, col))
                continue

            if ch in BRACKETS:
                line, col = self.line, self.column
                self._advance()
                tokens.append(Token(BRACKETS[ch], ch, line, col))
                continue

            if ch in DELIMITERS:
                line, col = self.line, self.column
                self._advance()
                tokens.append(Token(TokenType.DELIMITER, ch, line, col))
                continue

            # Multi-character operators
            matched_op = None
            for op in MULTI_CHAR_OPS:
                if self.source.startswith(op, self.pos):
                    matched_op = op
                    break

            if matched_op:
                line, col = self.line, self.column
                for _ in matched_op:
                    self._advance()
                tokens.append(Token(TokenType.OPERATOR, matched_op, line, col))
                continue

            # Single-character operators
            if ch in SINGLE_CHAR_OPS:
                line, col = self.line, self.column
                self._advance()
                tokens.append(Token(TokenType.OPERATOR, ch, line, col))
                continue

            # Unrecognized character
            err_line, err_col = self.line, self.column
            bad_char = self._advance()
            raise LexerError(
                message=f"Unexpected character '{bad_char}'",
                line=err_line,
                column=err_col,
                suggestion=f"Remove or replace invalid character '{bad_char}'."
            )

        # Append EOF token
        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    def _lex_number(self) -> Token:
        start_line, start_col = self.line, self.column
        num_str = ""

        # Handle hex (0x...), binary (0b...), octal (0o...)
        if self._peek() == "0" and self._peek(1).lower() in ("x", "b", "o"):
            num_str += self._advance()  # '0'
            num_str += self._advance()  # 'x' / 'b' / 'o'
            while self._peek().isalnum():
                num_str += self._advance()
            return Token(TokenType.NUMBER, num_str, start_line, start_col)

        has_dot = False
        while self.pos < self.length:
            ch = self._peek()
            if ch.isdigit():
                num_str += self._advance()
            elif ch == "." and not has_dot and self._peek(1).isdigit():
                has_dot = True
                num_str += self._advance()
            elif ch.lower() == "e" and (self._peek(1).isdigit() or self._peek(1) in "+-"):
                num_str += self._advance()
                if self._peek() in "+-":
                    num_str += self._advance()
                while self._peek().isdigit():
                    num_str += self._advance()
                break
            elif ch.lower() in ("f", "l", "u") and self.language in ("c", "cpp", "c++", "java"):
                # Numeric type suffix (e.g., 100L, 3.14f)
                num_str += self._advance()
            else:
                break

        return Token(TokenType.NUMBER, num_str, start_line, start_col)

    def _lex_identifier_or_keyword(self) -> Token:
        start_line, start_col = self.line, self.column
        ident = ""

        while self.pos < self.length:
            ch = self._peek()
            if ch.isalnum() or ch == "_" or (self.language in ("javascript", "js") and ch == "$"):
                ident += self._advance()
            else:
                break

        token_type = TokenType.KEYWORD if ident in self.keywords else TokenType.IDENTIFIER
        return Token(token_type, ident, start_line, start_col)

    def _lex_string(self) -> Token:
        quote = self._advance()
        start_line, start_col = self.line, self.column - 1
        content = [quote]

        # Check for triple quotes in Python
        is_triple = False
        if self.language in ("python", "py") and quote in ('"', "'") and self._peek() == quote and self._peek(1) == quote:
            is_triple = True
            content.append(self._advance())
            content.append(self._advance())
            target_closing = quote * 3
            while self.pos < self.length:
                if self.source.startswith(target_closing, self.pos):
                    content.append(self._advance())
                    content.append(self._advance())
                    content.append(self._advance())
                    return Token(TokenType.STRING, "".join(content), start_line, start_col)
                if self._peek() == "\\" and self.pos + 1 < self.length:
                    content.append(self._advance())
                    content.append(self._advance())
                else:
                    content.append(self._advance())

            raise LexerError(
                message=f"Unterminated triple-quoted string literal starting at line {start_line}, column {start_col}",
                line=start_line,
                column=start_col,
                suggestion=f"Close the string literal with matching {target_closing}."
            )

        # Single or double quotes (or JS template literals)
        is_template = (quote == "`")
        while self.pos < self.length:
            ch = self._peek()
            if ch == "\\":
                content.append(self._advance())
                if self.pos < self.length:
                    content.append(self._advance())
                continue

            if ch == quote:
                content.append(self._advance())
                return Token(TokenType.STRING, "".join(content), start_line, start_col)

            if ch == "\n" and not is_template:
                raise LexerError(
                    message=f"Unterminated string literal at line {start_line}, column {start_col}",
                    line=start_line,
                    column=start_col,
                    suggestion=f"Add closing quote {quote} before the end of the line."
                )

            content.append(self._advance())

        raise LexerError(
            message=f"Unterminated string literal reaching end of file",
            line=start_line,
            column=start_col,
            suggestion=f"Add closing quote {quote} to complete the string literal."
        )

    def _lex_line_comment(self) -> Token:
        start_line, start_col = self.line, self.column
        comment_text = ""
        while self.pos < self.length and self._peek() != "\n":
            comment_text += self._advance()
        return Token(TokenType.COMMENT, comment_text, start_line, start_col)

    def _lex_python_comment(self) -> Token:
        start_line, start_col = self.line, self.column
        comment_text = ""
        while self.pos < self.length and self._peek() != "\n":
            comment_text += self._advance()
        return Token(TokenType.COMMENT, comment_text, start_line, start_col)

    def _lex_block_comment(self) -> Token:
        start_line, start_col = self.line, self.column
        comment_text = self._advance() + self._advance()  # /*

        while self.pos < self.length:
            if self._peek() == "*" and self._peek(1) == "/":
                comment_text += self._advance() + self._advance()
                return Token(TokenType.COMMENT, comment_text, start_line, start_col)
            comment_text += self._advance()

        raise LexerError(
            message=f"Unterminated block comment starting at line {start_line}, column {start_col}",
            line=start_line,
            column=start_col,
            suggestion="Close the block comment with '*/'."
        )

    def _lex_preprocessor(self) -> Token:
        start_line, start_col = self.line, self.column
        text = ""
        while self.pos < self.length and self._peek() != "\n":
            text += self._advance()
        return Token(TokenType.PREPROCESSOR, text, start_line, start_col)


def tokenize(source: str, language: str = "javascript") -> List[Token]:
    """Convenience helper to tokenize source code."""
    lexer = Lexer(source, language)
    return lexer.tokenize()
