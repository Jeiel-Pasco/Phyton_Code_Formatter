"""Syntax Parser for Multi-Language Code Formatter.

Builds an Abstract Syntax Tree (AST) / Intermediate Representation from tokens.
Validates language grammar, supports nested structures, statements, expressions,
and preserves all comments within the AST.
"""

from typing import List, Optional, Any, Union
from backend.lexer import Token, TokenType
from backend.errors import SyntaxError


# =====================================================================
# AST Nodes
# =====================================================================

class ASTNode:
    """Base class for all AST nodes."""

    def __init__(self, line: int = 1, column: int = 1):
        self.line = line
        self.column = column
        self.leading_comments: List[str] = []
        self.trailing_comment: Optional[str] = None


class ProgramNode(ASTNode):
    """Root program node containing a sequence of top-level statements."""

    def __init__(self, body: List[ASTNode], language: str = "javascript"):
        super().__init__()
        self.body = body
        self.language = language


class BlockNode(ASTNode):
    """Code block enclosed in braces { ... } or an indented suite."""

    def __init__(self, statements: List[ASTNode], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.statements = statements


class CommentNode(ASTNode):
    """Represents a standalone or preserved comment."""

    def __init__(self, text: str, is_multiline: bool = False, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.text = text
        self.is_multiline = is_multiline


class PreprocessorNode(ASTNode):
    """C/C++ Preprocessor directive (#include, #define, etc.)."""

    def __init__(self, text: str, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.text = text


class VarDeclNode(ASTNode):
    """Variable or constant declaration."""

    def __init__(
        self,
        modifiers: List[str],
        type_name: Optional[str],
        name: str,
        init_expr: Optional[ASTNode] = None,
        line: int = 1,
        column: int = 1
    ):
        super().__init__(line, column)
        self.modifiers = modifiers
        self.type_name = type_name
        self.name = name
        self.init_expr = init_expr


class IfStatementNode(ASTNode):
    """If-else conditional statement."""

    def __init__(
        self,
        condition: ASTNode,
        then_branch: ASTNode,
        else_branch: Optional[ASTNode] = None,
        line: int = 1,
        column: int = 1
    ):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch


class WhileStatementNode(ASTNode):
    """While loop."""

    def __init__(
        self,
        condition: ASTNode,
        body: ASTNode,
        line: int = 1,
        column: int = 1
    ):
        super().__init__(line, column)
        self.condition = condition
        self.body = body


class ForStatementNode(ASTNode):
    """For loop."""

    def __init__(
        self,
        init: Optional[ASTNode],
        condition: Optional[ASTNode],
        update: Optional[ASTNode],
        body: ASTNode,
        line: int = 1,
        column: int = 1
    ):
        super().__init__(line, column)
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body


class FunctionDefNode(ASTNode):
    """Function or method definition."""

    def __init__(
        self,
        name: str,
        params: List[str],
        body: ASTNode,
        return_type: Optional[str] = None,
        modifiers: Optional[List[str]] = None,
        is_async: bool = False,
        line: int = 1,
        column: int = 1
    ):
        super().__init__(line, column)
        self.name = name
        self.params = params
        self.body = body
        self.return_type = return_type
        self.modifiers = modifiers or []
        self.is_async = is_async


class ClassDefNode(ASTNode):
    """Class definition."""

    def __init__(
        self,
        name: str,
        bases: List[str],
        body: ASTNode,
        modifiers: Optional[List[str]] = None,
        line: int = 1,
        column: int = 1
    ):
        super().__init__(line, column)
        self.name = name
        self.bases = bases
        self.body = body
        self.modifiers = modifiers or []


class ReturnStatementNode(ASTNode):
    """Return statement."""

    def __init__(self, value: Optional[ASTNode] = None, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.value = value


class ExpressionStatementNode(ASTNode):
    """Expression executed as a standalone statement."""

    def __init__(self, expression: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.expression = expression


class BinaryOpNode(ASTNode):
    """Binary operation (e.g., a + b, x > 5, y = 10)."""

    def __init__(self, left: ASTNode, op: str, right: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.left = left
        self.op = op
        self.right = right


class UnaryOpNode(ASTNode):
    """Unary operation (e.g., !x, -5, x++, ++y)."""

    def __init__(self, op: str, operand: ASTNode, is_postfix: bool = False, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.op = op
        self.operand = operand
        self.is_postfix = is_postfix


class CallNode(ASTNode):
    """Function / method call."""

    def __init__(self, callee: ASTNode, args: List[ASTNode], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.callee = callee
        self.args = args


class MemberAccessNode(ASTNode):
    """Member or property access (e.g., object.property or std::cout)."""

    def __init__(self, obj: ASTNode, member: str, op: str = ".", line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.obj = obj
        self.member = member
        self.op = op


class IndexAccessNode(ASTNode):
    """Array or dictionary subscript indexing (e.g., arr[i])."""

    def __init__(self, obj: ASTNode, index: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.obj = obj
        self.index = index


class LiteralNode(ASTNode):
    """Literal constant (number, string, boolean)."""

    def __init__(self, value: str, lit_type: str = "string", line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.value = value
        self.lit_type = lit_type


class IdentifierNode(ASTNode):
    """Variable or symbol identifier."""

    def __init__(self, name: str, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.name = name


class GroupNode(ASTNode):
    """Parenthesized expression ( expr )."""

    def __init__(self, expression: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.expression = expression


# =====================================================================
# Parser Implementation
# =====================================================================

PRECEDENCE = {
    "=": 1, "+=": 1, "-=": 1, "*=": 1, "/=": 1, "%=": 1, "<<=": 1, ">>=": 1, "&=": 1, "|=": 1, "^=": 1,
    "||": 2, "or": 2,
    "&&": 3, "and": 3,
    "|": 4,
    "^": 5,
    "&": 6,
    "==": 7, "!=": 7, "===": 7, "!==": 7,
    "<": 8, "<=": 8, ">": 8, ">=": 8,
    "<<": 9, ">>": 9,
    "+": 10, "-": 10,
    "*": 11, "/": 11, "%": 11,
}

TYPE_KEYWORDS = {
    "int", "float", "double", "char", "void", "short", "long", "unsigned",
    "signed", "bool", "boolean", "string", "String", "size_t", "auto",
    "var", "let", "const", "byte"
}

MODIFIER_KEYWORDS = {
    "public", "private", "protected", "static", "final", "const",
    "volatile", "inline", "virtual", "extern", "register", "async"
}


class Parser:
    """Recursive descent syntax parser."""

    def __init__(self, tokens: List[Token], language: str = "javascript"):
        self.tokens = tokens
        self.language = language.lower()
        self.pos = 0
        self.total = len(tokens)

    def _current(self) -> Token:
        if self.pos < self.total:
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < self.total:
            return self.tokens[idx]
        return self.tokens[-1]

    def _advance(self) -> Token:
        tok = self._current()
        if self.pos < self.total - 1:
            self.pos += 1
        return tok

    def _check(self, type_: TokenType, value: Optional[str] = None) -> bool:
        tok = self._current()
        if tok.type != type_:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def _match(self, type_: TokenType, value: Optional[str] = None) -> bool:
        if self._check(type_, value):
            self._advance()
            return True
        return False

    def _expect(self, type_: TokenType, value: Optional[str] = None, suggestion: Optional[str] = None) -> Token:
        tok = self._current()
        if tok.type == type_ and (value is None or tok.value == value):
            return self._advance()

        val_repr = f"'{value}'" if value else type_.name
        curr_repr = f"'{tok.value}'" if tok.value else tok.type.name
        sugg = suggestion or f"Expected {val_repr} but found {curr_repr}."
        raise SyntaxError(
            message=f"expected {val_repr} but found {curr_repr}",
            line=tok.line,
            column=tok.column,
            suggestion=sugg
        )

    def parse(self) -> ProgramNode:
        """Parse all tokens into a ProgramNode."""
        statements: List[ASTNode] = []

        while not self._check(TokenType.EOF):
            # Skip empty newlines in Python
            if self._match(TokenType.NEWLINE):
                continue

            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)

        return ProgramNode(body=statements, language=self.language)

    def _parse_statement(self) -> ASTNode:
        tok = self._current()

        # Preprocessor directive
        if tok.type == TokenType.PREPROCESSOR:
            self._advance()
            return PreprocessorNode(tok.value, tok.line, tok.column)

        # Standalone comment
        if tok.type == TokenType.COMMENT:
            self._advance()
            is_multiline = tok.value.startswith("/*")
            return CommentNode(tok.value, is_multiline=is_multiline, line=tok.line, column=tok.column)

        # Block statement { ... }
        if tok.type == TokenType.LBRACE:
            return self._parse_block()

        # Keywords statements
        if tok.type == TokenType.KEYWORD:
            val = tok.value
            if val == "if":
                return self._parse_if_statement()
            if val == "while":
                return self._parse_while_statement()
            if val == "for":
                return self._parse_for_statement()
            if val == "return":
                return self._parse_return_statement()
            if val in ("function", "def"):
                return self._parse_function_def()
            if val == "class":
                return self._parse_class_def()

        # Function definition (C-style: int add(int a) { ... } or int main() { ... })
        if self._is_c_function_def():
            return self._parse_c_function_def()

        # Variable declarations (C, C++, Java, JS let/const/var)
        if self._is_var_declaration():
            return self._parse_var_declaration()

        # Expression statement
        expr = self._parse_expression()
        self._consume_statement_terminator()
        return ExpressionStatementNode(expr, expr.line, expr.column)

    def _consume_statement_terminator(self):
        """Consume semicolon or newline."""
        if self._check(TokenType.DELIMITER, ";"):
            self._advance()
        elif self.language in ("python", "py"):
            if self._check(TokenType.NEWLINE):
                self._advance()
        # In JS/C++, if at EOF or followed by '}', semicolon might be omitted
        elif self._check(TokenType.RBRACE) or self._check(TokenType.EOF):
            pass
        elif self.language in ("c", "cpp", "c++", "java"):
            # Semicolon strictly expected in C/C++/Java
            curr = self._current()
            raise SyntaxError(
                message=f"expected ';' after statement but found '{curr.value}'",
                line=curr.line,
                column=curr.column,
                suggestion="Add a semicolon ';' to terminate the statement."
            )

    def _parse_block(self) -> BlockNode:
        start_tok = self._expect(TokenType.LBRACE, "{")
        statements: List[ASTNode] = []

        while not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            if self._match(TokenType.NEWLINE):
                continue
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)

        self._expect(TokenType.RBRACE, "}", suggestion="Close the block with '}'.")
        return BlockNode(statements, start_tok.line, start_tok.column)

    def _parse_if_statement(self) -> IfStatementNode:
        start_tok = self._advance()  # 'if'

        # Parse condition
        if self.language in ("python", "py"):
            cond = self._parse_expression()
            self._expect(TokenType.DELIMITER, ":", suggestion="Add ':' after if condition.")
            then_branch = self._parse_suite()
            while self._match(TokenType.NEWLINE):
                pass
            else_branch = None
            if self._match(TokenType.KEYWORD, "elif"):
                # Treat elif as nested if
                else_branch = self._parse_if_statement()
            elif self._match(TokenType.KEYWORD, "else"):
                self._expect(TokenType.DELIMITER, ":", suggestion="Add ':' after else.")
                else_branch = self._parse_suite()
            return IfStatementNode(cond, then_branch, else_branch, start_tok.line, start_tok.column)
        else:
            self._expect(TokenType.LPAREN, "(", suggestion="Condition must be wrapped in '('.")
            cond = self._parse_expression()
            self._expect(
                TokenType.RPAREN,
                ")",
                suggestion="Fix the source and format again."
            )
            then_branch = self._parse_statement_or_block()

            else_branch = None
            if self._match(TokenType.KEYWORD, "else"):
                else_branch = self._parse_statement_or_block()

            return IfStatementNode(cond, then_branch, else_branch, start_tok.line, start_tok.column)

    def _parse_while_statement(self) -> WhileStatementNode:
        start_tok = self._advance()  # 'while'

        if self.language in ("python", "py"):
            cond = self._parse_expression()
            self._expect(TokenType.DELIMITER, ":", suggestion="Add ':' after while condition.")
            body = self._parse_suite()
        else:
            self._expect(TokenType.LPAREN, "(", suggestion="While condition must be enclosed in '('.")
            cond = self._parse_expression()
            self._expect(TokenType.RPAREN, ")", suggestion="Close condition with ')'.")
            body = self._parse_statement_or_block()

        return WhileStatementNode(cond, body, start_tok.line, start_tok.column)

    def _parse_for_statement(self) -> ForStatementNode:
        start_tok = self._advance()  # 'for'

        if self.language in ("python", "py"):
            # for target in iterable:
            target = self._parse_expression()
            self._expect(TokenType.KEYWORD, "in")
            iter_expr = self._parse_expression()
            self._expect(TokenType.DELIMITER, ":")
            body = self._parse_suite()
            in_cond = BinaryOpNode(target, "in", iter_expr, target.line, target.column)
            return ForStatementNode(None, in_cond, None, body, start_tok.line, start_tok.column)

        self._expect(TokenType.LPAREN, "(", suggestion="For loop clauses must be enclosed in '('.")

        # 1. init
        init = None
        if not self._check(TokenType.DELIMITER, ";"):
            if self._is_var_declaration():
                init = self._parse_var_declaration(consume_semi=False)
            else:
                init = self._parse_expression()
        self._expect(TokenType.DELIMITER, ";", suggestion="For loop init must end with ';'.")

        # 2. condition
        cond = None
        if not self._check(TokenType.DELIMITER, ";"):
            cond = self._parse_expression()
        self._expect(TokenType.DELIMITER, ";", suggestion="For loop condition must end with ';'.")

        # 3. update
        update = None
        if not self._check(TokenType.RPAREN, ")"):
            update = self._parse_expression()
        self._expect(TokenType.RPAREN, ")", suggestion="Close for loop clauses with ')'.")

        body = self._parse_statement_or_block()
        return ForStatementNode(init, cond, update, body, start_tok.line, start_tok.column)

    def _parse_return_statement(self) -> ReturnStatementNode:
        start_tok = self._advance()  # 'return'
        val = None
        if not self._check(TokenType.DELIMITER, ";") and not self._check(TokenType.NEWLINE) and not self._check(TokenType.RBRACE):
            val = self._parse_expression()
        self._consume_statement_terminator()
        return ReturnStatementNode(val, start_tok.line, start_tok.column)

    def _parse_function_def(self) -> FunctionDefNode:
        start_tok = self._advance()  # 'function' or 'def'
        name_tok = self._expect(TokenType.IDENTIFIER, suggestion="Provide a valid function name.")
        self._expect(TokenType.LPAREN, "(")

        params: List[str] = []
        while not self._check(TokenType.RPAREN) and not self._check(TokenType.EOF):
            param_tok = self._advance()
            params.append(param_tok.value)
            if self._check(TokenType.DELIMITER, ","):
                self._advance()

        self._expect(TokenType.RPAREN, ")")

        if self.language in ("python", "py"):
            self._expect(TokenType.DELIMITER, ":")
            body = self._parse_suite()
        else:
            body = self._parse_statement_or_block()

        return FunctionDefNode(
            name=name_tok.value,
            params=params,
            body=body,
            line=start_tok.line,
            column=start_tok.column
        )

    def _parse_class_def(self) -> ClassDefNode:
        start_tok = self._advance()  # 'class'
        name_tok = self._expect(TokenType.IDENTIFIER, suggestion="Provide a class name.")
        bases: List[str] = []

        if self._match(TokenType.LPAREN, "("):
            while not self._check(TokenType.RPAREN) and not self._check(TokenType.EOF):
                bases.append(self._advance().value)
                if self._check(TokenType.DELIMITER, ","):
                    self._advance()
            self._expect(TokenType.RPAREN, ")")
        elif self._match(TokenType.KEYWORD, "extends"):
            bases.append(self._expect(TokenType.IDENTIFIER).value)

        if self.language in ("python", "py"):
            self._expect(TokenType.DELIMITER, ":")
            body = self._parse_suite()
        else:
            body = self._parse_block()

        return ClassDefNode(name=name_tok.value, bases=bases, body=body, line=start_tok.line, column=start_tok.column)

    def _parse_suite(self) -> ASTNode:
        """Parse indented suite or block for Python."""
        # For simplicity, if next is block or statement, parse statements until dedent or end
        stmts: List[ASTNode] = []
        if self._check(TokenType.LBRACE):
            return self._parse_block()

        # Read single statement or multiple statements
        while self._match(TokenType.NEWLINE):
            pass

        stmt = self._parse_statement()
        stmts.append(stmt)
        return BlockNode(stmts, stmt.line, stmt.column)

    def _parse_statement_or_block(self) -> ASTNode:
        if self._check(TokenType.LBRACE):
            return self._parse_block()
        stmt = self._parse_statement()
        # Wrap single statement in a block for consistent formatting
        return BlockNode([stmt], stmt.line, stmt.column)

    def _is_var_declaration(self) -> bool:
        tok = self._current()
        if tok.type == TokenType.KEYWORD:
            if tok.value in ("let", "const", "var"):
                return True
            if tok.value in TYPE_KEYWORDS or tok.value in MODIFIER_KEYWORDS:
                # E.g. "int x" or "public static int x"
                return True
        # E.g. "string name = ..."
        if tok.type in (TokenType.KEYWORD, TokenType.IDENTIFIER) and self._peek().type == TokenType.IDENTIFIER:
            # Check 2 tokens ahead: "type name = ..." or "type name;"
            p2 = self._peek(2)
            if p2.type in (TokenType.DELIMITER, TokenType.OPERATOR, TokenType.EOF):
                return True
        return False

    def _parse_var_declaration(self, consume_semi: bool = True) -> VarDeclNode:
        modifiers: List[str] = []
        while self._current().value in MODIFIER_KEYWORDS:
            modifiers.append(self._advance().value)

        type_name = None
        if self._current().value in TYPE_KEYWORDS:
            type_name = self._advance().value
        elif self._peek().type == TokenType.IDENTIFIER:
            type_name = self._advance().value

        name_tok = self._expect(TokenType.IDENTIFIER, suggestion="Provide a variable name.")
        init_expr = None
        if self._match(TokenType.OPERATOR, "="):
            init_expr = self._parse_expression()

        if consume_semi:
            self._consume_statement_terminator()

        return VarDeclNode(
            modifiers=modifiers,
            type_name=type_name,
            name=name_tok.value,
            init_expr=init_expr,
            line=name_tok.line,
            column=name_tok.column
        )

    def _is_c_function_def(self) -> bool:
        # Check pattern: [type] name '(' ... ')' '{'
        idx = self.pos
        if self.tokens[idx].type == TokenType.KEYWORD and self.tokens[idx].value in TYPE_KEYWORDS:
            idx += 1
        if idx < self.total and self.tokens[idx].type == TokenType.IDENTIFIER:
            idx += 1
            if idx < self.total and self.tokens[idx].type == TokenType.LPAREN:
                depth = 1
                idx += 1
                while idx < self.total and depth > 0:
                    if self.tokens[idx].type == TokenType.LPAREN:
                        depth += 1
                    elif self.tokens[idx].type == TokenType.RPAREN:
                        depth -= 1
                    idx += 1
                if idx < self.total and self.tokens[idx].type == TokenType.LBRACE:
                    return True
        return False

    def _parse_c_function_def(self) -> FunctionDefNode:
        return_type = None
        if self._current().value in TYPE_KEYWORDS:
            return_type = self._advance().value

        name_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.LPAREN, "(")

        params: List[str] = []
        current_param = []
        while not self._check(TokenType.RPAREN) and not self._check(TokenType.EOF):
            tok = self._advance()
            if tok.type == TokenType.DELIMITER and tok.value == ",":
                if current_param:
                    params.append(" ".join(current_param))
                    current_param = []
            else:
                current_param.append(tok.value)

        if current_param:
            params.append(" ".join(current_param))

        self._expect(TokenType.RPAREN, ")")
        body = self._parse_block()
        return FunctionDefNode(
            name=name_tok.value,
            params=params,
            body=body,
            return_type=return_type,
            line=name_tok.line,
            column=name_tok.column
        )

    # =====================================================================
    # Expression Parsing
    # =====================================================================

    def _parse_expression(self, min_prec: int = 0) -> ASTNode:
        left = self._parse_primary()

        while True:
            tok = self._current()
            op = tok.value

            # Postfix unary operators (x++, x--)
            if tok.type == TokenType.OPERATOR and op in ("++", "--"):
                self._advance()
                left = UnaryOpNode(op, left, is_postfix=True, line=tok.line, column=tok.column)
                continue

            # Method or member access (obj.foo or ptr->bar or std::cout)
            if (tok.type == TokenType.DELIMITER and op == ".") or (tok.type == TokenType.OPERATOR and op in ("->", "::")):
                self._advance()
                member_tok = self._advance()
                left = MemberAccessNode(left, member_tok.value, op=op, line=tok.line, column=tok.column)
                continue

            # Function call
            if tok.type == TokenType.LPAREN:
                self._advance()
                args: List[ASTNode] = []
                while not self._check(TokenType.RPAREN) and not self._check(TokenType.EOF):
                    args.append(self._parse_expression())
                    if self._check(TokenType.DELIMITER, ","):
                        self._advance()
                self._expect(TokenType.RPAREN, ")")
                left = CallNode(left, args, line=tok.line, column=tok.column)
                continue

            # Index access arr[i]
            if tok.type == TokenType.LBRACKET:
                self._advance()
                idx_expr = self._parse_expression()
                self._expect(TokenType.RBRACKET, "]")
                left = IndexAccessNode(left, idx_expr, line=tok.line, column=tok.column)
                continue

            # Binary operator
            prec = PRECEDENCE.get(op, 0)
            if tok.type != TokenType.OPERATOR or prec <= min_prec:
                break

            self._advance()
            # Right associative for assignment
            next_min_prec = prec if op in ("=", "+=", "-=", "*=", "/=") else prec
            right = self._parse_expression(next_min_prec)
            left = BinaryOpNode(left, op, right, line=tok.line, column=tok.column)

        return left

    def _parse_primary(self) -> ASTNode:
        tok = self._current()

        # Standalone inline comment
        if tok.type == TokenType.COMMENT:
            self._advance()
            return CommentNode(tok.value, line=tok.line, column=tok.column)

        # Prefix unary operators (+, -, !, ~, ++, --, *, &)
        if tok.type == TokenType.OPERATOR and tok.value in ("+", "-", "!", "~", "++", "--", "*", "&"):
            op_tok = self._advance()
            operand = self._parse_primary()
            return UnaryOpNode(op_tok.value, operand, is_postfix=False, line=op_tok.line, column=op_tok.column)

        # Parenthesized expression ( expr )
        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN, ")")
            return GroupNode(expr, line=tok.line, column=tok.column)

        # Number literal
        if tok.type == TokenType.NUMBER:
            self._advance()
            return LiteralNode(tok.value, lit_type="number", line=tok.line, column=tok.column)

        # String literal
        if tok.type == TokenType.STRING:
            self._advance()
            return LiteralNode(tok.value, lit_type="string", line=tok.line, column=tok.column)

        # Boolean and null literals
        if tok.type == TokenType.KEYWORD and tok.value in ("true", "false", "null", "undefined", "True", "False", "None"):
            self._advance()
            return LiteralNode(tok.value, lit_type="boolean", line=tok.line, column=tok.column)

        # Identifiers
        if tok.type in (TokenType.IDENTIFIER, TokenType.KEYWORD):
            self._advance()
            return IdentifierNode(tok.value, line=tok.line, column=tok.column)

        # Unexpected token
        raise SyntaxError(
            message=f"unexpected token '{tok.value}'",
            line=tok.line,
            column=tok.column,
            suggestion="Check expression syntax and valid identifiers."
        )


def parse(tokens: List[Token], language: str = "javascript") -> ProgramNode:
    """Helper to parse a token sequence into an AST."""
    parser = Parser(tokens, language)
    return parser.parse()
