"""Code Formatter / Pretty Printer for Multi-Language AST.

Generates properly formatted, indented, and spaced source code from AST nodes.
Supports configurable indentation, operator spacing, brace formatting, comment preservation,
and language-specific syntax rules.
"""

from typing import List, Optional, Union
from backend.parser import (
    ASTNode, ProgramNode, BlockNode, CommentNode, PreprocessorNode,
    VarDeclNode, IfStatementNode, WhileStatementNode, ForStatementNode,
    FunctionDefNode, ClassDefNode, ReturnStatementNode, ExpressionStatementNode,
    BinaryOpNode, UnaryOpNode, CallNode, MemberAccessNode, IndexAccessNode,
    LiteralNode, IdentifierNode, GroupNode
)


class CodePrinter:
    """Pretty printer that formats AST into clean source code."""

    def __init__(
        self,
        indent_size: int = 4,
        indent_style: str = "spaces",
        max_line_length: int = 80
    ):
        self.indent_size = indent_size
        self.indent_style = indent_style
        self.max_line_length = max_line_length
        self.indent_unit = "\t" if indent_style == "tabs" else (" " * indent_size)

    def print(self, node: ASTNode, language: str = "javascript") -> str:
        """Format an AST node into clean source code string."""
        lang = language.lower()
        if isinstance(node, ProgramNode):
            return self._format_program(node, lang)
        return self._format_node(node, 0, lang)

    def _indent_str(self, level: int) -> str:
        return self.indent_unit * level

    def _format_program(self, prog: ProgramNode, lang: str) -> str:
        lines: List[str] = []
        is_python = lang in ("python", "py")

        prev_node_type = None
        for i, stmt in enumerate(prog.body):
            curr_type = type(stmt)

            # Add blank line before control structures, functions, classes, or after blocks
            if i > 0:
                is_major_block = curr_type in (
                    IfStatementNode, WhileStatementNode, ForStatementNode,
                    FunctionDefNode, ClassDefNode
                )
                prev_was_major = prev_node_type in (
                    IfStatementNode, WhileStatementNode, ForStatementNode,
                    FunctionDefNode, ClassDefNode
                )
                if is_major_block or prev_was_major:
                    lines.append("")

            formatted = self._format_node(stmt, 0, lang)
            if formatted:
                lines.append(formatted)

            prev_node_type = curr_type

        # Ensure single trailing newline
        result = "\n".join(lines).rstrip() + "\n"
        return result

    def _format_node(self, node: ASTNode, level: int, lang: str) -> str:
        is_python = lang in ("python", "py")
        indent = self._indent_str(level)

        if isinstance(node, CommentNode):
            return f"{indent}{node.text}"

        if isinstance(node, PreprocessorNode):
            return f"{indent}{node.text}"

        if isinstance(node, VarDeclNode):
            parts = []
            if node.modifiers:
                parts.extend(node.modifiers)
            if node.type_name:
                parts.append(node.type_name)
            parts.append(node.name)
            decl_str = " ".join(parts)
            if node.init_expr:
                val_str = self._format_expression(node.init_expr, lang)
                decl_str += f" = {val_str}"
            semi = "" if is_python else ";"
            return f"{indent}{decl_str}{semi}"

        if isinstance(node, IfStatementNode):
            cond_str = self._format_expression(node.condition, lang)
            if is_python:
                res = f"{indent}if {cond_str}:\n"
                res += self._format_suite(node.then_branch, level + 1, lang)
                if node.else_branch:
                    if isinstance(node.else_branch, IfStatementNode):
                        elif_str = self._format_node(node.else_branch, level, lang).lstrip()
                        res += f"\n{indent}el{elif_str}"
                    else:
                        res += f"\n{indent}else:\n"
                        res += self._format_suite(node.else_branch, level + 1, lang)
                return res
            else:
                res = f"{indent}if ({cond_str}) "
                res += self._format_brace_block(node.then_branch, level, lang)
                if node.else_branch:
                    res += " else "
                    if isinstance(node.else_branch, IfStatementNode):
                        res += self._format_node(node.else_branch, level, lang).lstrip()
                    else:
                        res += self._format_brace_block(node.else_branch, level, lang)
                return res

        if isinstance(node, WhileStatementNode):
            cond_str = self._format_expression(node.condition, lang)
            if is_python:
                res = f"{indent}while {cond_str}:\n"
                res += self._format_suite(node.body, level + 1, lang)
                return res
            else:
                res = f"{indent}while ({cond_str}) "
                res += self._format_brace_block(node.body, level, lang)
                return res

        if isinstance(node, ForStatementNode):
            if is_python:
                cond_str = self._format_expression(node.condition, lang)
                res = f"{indent}for {cond_str}:\n"
                res += self._format_suite(node.body, level + 1, lang)
                return res
            else:
                init_str = ""
                if node.init:
                    if isinstance(node.init, VarDeclNode):
                        init_str = self._format_node(node.init, 0, lang).rstrip(";")
                    else:
                        init_str = self._format_expression(node.init, lang)

                cond_str = self._format_expression(node.condition, lang) if node.condition else ""
                update_str = self._format_expression(node.update, lang) if node.update else ""

                res = f"{indent}for ({init_str}; {cond_str}; {update_str}) "
                res += self._format_brace_block(node.body, level, lang)
                return res

        if isinstance(node, FunctionDefNode):
            params_str = ", ".join(node.params)
            if is_python:
                res = f"{indent}def {node.name}({params_str}):\n"
                res += self._format_suite(node.body, level + 1, lang)
                return res
            else:
                prefix = []
                if node.modifiers:
                    prefix.extend(node.modifiers)
                if node.is_async:
                    prefix.append("async")
                if lang in ("javascript", "js"):
                    prefix.append("function")
                elif node.return_type:
                    prefix.append(node.return_type)

                p_str = (" ".join(prefix) + " ") if prefix else ""
                res = f"{indent}{p_str}{node.name}({params_str}) "
                res += self._format_brace_block(node.body, level, lang)
                return res

        if isinstance(node, ClassDefNode):
            bases_str = f"({', '.join(node.bases)})" if node.bases else ""
            if is_python:
                res = f"{indent}class {node.name}{bases_str}:\n"
                res += self._format_suite(node.body, level + 1, lang)
                return res
            else:
                ext_str = f" extends {node.bases[0]}" if node.bases else ""
                res = f"{indent}class {node.name}{ext_str} "
                res += self._format_brace_block(node.body, level, lang)
                return res

        if isinstance(node, ReturnStatementNode):
            val_str = f" {self._format_expression(node.value, lang)}" if node.value else ""
            semi = "" if is_python else ";"
            return f"{indent}return{val_str}{semi}"

        if isinstance(node, ExpressionStatementNode):
            expr_str = self._format_expression(node.expression, lang)
            semi = "" if is_python else ";"
            return f"{indent}{expr_str}{semi}"

        if isinstance(node, BlockNode):
            if is_python:
                return self._format_suite(node, level, lang)
            return self._format_brace_block(node, level, lang)

        return f"{indent}{self._format_expression(node, lang)}"

    def _format_brace_block(self, block: ASTNode, level: int, lang: str) -> str:
        """Format a block enclosed in curly braces { ... }."""
        stmts = block.statements if isinstance(block, BlockNode) else [block]
        if not stmts:
            return "{\n" + self._indent_str(level) + "}"

        lines = ["{"]
        inner_level = level + 1
        for s in stmts:
            formatted_stmt = self._format_node(s, inner_level, lang)
            if formatted_stmt:
                lines.append(formatted_stmt)

        lines.append(self._indent_str(level) + "}")
        return "\n".join(lines)

    def _format_suite(self, block: ASTNode, level: int, lang: str) -> str:
        """Format an indented block suite for Python."""
        stmts = block.statements if isinstance(block, BlockNode) else [block]
        if not stmts:
            return self._indent_str(level) + "pass"

        lines = []
        for s in stmts:
            formatted_stmt = self._format_node(s, level, lang)
            if formatted_stmt:
                lines.append(formatted_stmt)
        return "\n".join(lines)

    def _format_expression(self, expr: ASTNode, lang: str) -> str:
        """Format expressions with standardized operator spacing."""
        if expr is None:
            return ""

        if isinstance(expr, LiteralNode):
            return expr.value

        if isinstance(expr, IdentifierNode):
            return expr.name

        if isinstance(expr, GroupNode):
            inner = self._format_expression(expr.expression, lang)
            return f"({inner})"

        if isinstance(expr, BinaryOpNode):
            left_str = self._format_expression(expr.left, lang)
            right_str = self._format_expression(expr.right, lang)
            # Consistent spacing around binary operators
            return f"{left_str} {expr.op} {right_str}"

        if isinstance(expr, UnaryOpNode):
            operand_str = self._format_expression(expr.operand, lang)
            if expr.is_postfix:
                return f"{operand_str}{expr.op}"
            return f"{expr.op}{operand_str}"

        if isinstance(expr, CallNode):
            callee_str = self._format_expression(expr.callee, lang)
            args_str = ", ".join(self._format_expression(a, lang) for a in expr.args)
            return f"{callee_str}({args_str})"

        if isinstance(expr, MemberAccessNode):
            obj_str = self._format_expression(expr.obj, lang)
            return f"{obj_str}{expr.op}{expr.member}"

        if isinstance(expr, IndexAccessNode):
            obj_str = self._format_expression(expr.obj, lang)
            idx_str = self._format_expression(expr.index, lang)
            return f"{obj_str}[{idx_str}]"

        if isinstance(expr, CommentNode):
            return expr.text

        return str(getattr(expr, "value", ""))


def format_ast(
    node: ASTNode,
    language: str = "javascript",
    indent_size: int = 4,
    indent_style: str = "spaces",
    max_line_length: int = 80
) -> str:
    """Convenience helper to format an AST into code."""
    printer = CodePrinter(
        indent_size=indent_size,
        indent_style=indent_style,
        max_line_length=max_line_length
    )
    return printer.print(node, language)
