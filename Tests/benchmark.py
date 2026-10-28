"""Automated Testing and Benchmarking Suite for Code Formatter.

Evaluates formatting correctness, idempotency, comment & string preservation,
comprehensive error handling, and latency benchmarks across Python, JavaScript, Java, C, and C++.
"""

import sys
import os
import time
from typing import List, Dict, Any

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.pipeline import format_code, SUPPORTED_LANGUAGES
from backend.errors import (
    FormatterException, LexerError, SyntaxError, UnsupportedLanguageError
)


class BenchmarkRunner:
    """Comprehensive test and benchmark runner."""

    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def assert_true(self, condition: bool, test_name: str, details: str = ""):
        if condition:
            self.tests_passed += 1
            print(f"  [PASS] {test_name}")
        else:
            self.tests_failed += 1
            msg = f"  [FAIL] {test_name}: {details}"
            print(msg)
            self.failures.append(msg)

    def run_all(self):
        print("=" * 70)
        print("          CODE FORMATTER AUTOMATED TEST & BENCHMARK SUITE          ")
        print("=" * 70)

        self.test_correctness_and_comments()
        self.test_multi_language_support()
        self.test_idempotency_and_stability()
        self.test_error_handling()
        self.test_performance_benchmarks()

        print("\n" + "=" * 70)
        print("                        BENCHMARK SUMMARY                         ")
        print("=" * 70)
        print(f"  Total Passed:  {self.tests_passed}")
        print(f"  Total Failed:  {self.tests_failed}")
        if self.failures:
            print("\n  Failures recorded:")
            for f in self.failures:
                print(f"    - {f}")
        else:
            print("\n  All tests passed successfully! System is fully functional.")
        print("=" * 70)

        return self.tests_failed == 0

    def test_correctness_and_comments(self):
        print("\n[SECTION 1: Formatting Correctness & Comment Preservation]")

        # Test 1: Mockup C snippet test
        mockup_source = (
            "// greet the user\n"
            "int x=10;string name = \"Ana\";\n"
            "if(x>5){print(\"big \"+name);}else{\n"
            "print(\"small\");}\n"
            "while(x>0){x=x-1;}"
        )
        res = format_code(mockup_source, language="c", indent_size=4)
        self.assert_true(res["success"], "Mockup C Snippet Formatted Successfully")
        self.assert_true("// greet the user" in res["formatted_code"], "Comment Preserved in Output")
        self.assert_true("x = 10;" in res["formatted_code"], "Operator Spacing in Variable Assignment")
        self.assert_true("if (x > 5) {" in res["formatted_code"], "If Condition and Brace Spacing")
        self.assert_true("    print(\"big \" + name);" in res["formatted_code"], "Indentation and Binary Operator Spacing")
        self.assert_true("} else {" in res["formatted_code"], "Else Block Formatting")
        self.assert_true("while (x > 0) {" in res["formatted_code"], "While Condition Spacing")
        self.assert_true(res["comments_preserved"] == 1, "Comment Count Correctness")

    def test_multi_language_support(self):
        print("\n[SECTION 2: Multi-Language Syntax Support]")

        # Python
        py_source = "# py test\ndef add(a, b):\n    if a>0:\n        return a+b\n    else:\n        return b"
        res_py = format_code(py_source, language="python", indent_size=4)
        self.assert_true(res_py["success"], "Python Formatting Success")
        self.assert_true("def add(a, b):" in res_py["formatted_code"], "Python Function Header Formatting")
        self.assert_true("# py test" in res_py["formatted_code"], "Python Comment Preservation")

        # JavaScript
        js_source = "function test(x){if(x===1){return true;}else{return false;}}"
        res_js = format_code(js_source, language="javascript", indent_size=2)
        self.assert_true(res_js["success"], "JavaScript Formatting Success (2-space indent)")
        self.assert_true("function test(x) {" in res_js["formatted_code"], "JavaScript Function Spacing")
        self.assert_true("  return true;" in res_js["formatted_code"], "JavaScript 2-space Indentation")

        # Java
        java_source = "int val=42;if(val!=0){System.out.println(\"ok\");}"
        res_java = format_code(java_source, language="java", indent_size=4)
        self.assert_true(res_java["success"], "Java Formatting Success")
        self.assert_true("int val = 42;" in res_java["formatted_code"], "Java Variable Declaration Spacing")

        # C++
        cpp_source = "#include <iostream>\nint main(){int x=5;return 0;}"
        res_cpp = format_code(cpp_source, language="cpp", indent_size=4)
        self.assert_true(res_cpp["success"], "C++ Formatting Success with Preprocessor Directive")
        self.assert_true("#include <iostream>" in res_cpp["formatted_code"], "C++ Preprocessor Preserved")

    def test_idempotency_and_stability(self):
        print("\n[SECTION 3: Idempotency & Whitespace Stability]")

        source = (
            "int a=1;int b=2;\n"
            "if(a<b){\n"
            "    print(\"yes\");\n"
            "}\n"
        )
        res1 = format_code(source, language="c")
        self.assert_true(res1["success"], "Pass 1 Formatting")

        res2 = format_code(res1["formatted_code"], language="c")
        self.assert_true(res2["success"], "Pass 2 Formatting (Idempotency)")
        self.assert_true(
            res1["formatted_code"] == res2["formatted_code"],
            "Idempotency Invariant: format(format(code)) == format(code)"
        )

    def test_error_handling(self):
        print("\n[SECTION 4: Robust Error Handling]")

        # Empty input
        res_empty = format_code("", language="javascript")
        self.assert_true(res_empty["success"] and res_empty["formatted_code"] == "", "Empty Input Handling")

        # Syntax error: missing closing parenthesis
        syntax_bad = "if(x>5 { print(\"err\"); }"
        res_err = format_code(syntax_bad, language="c")
        self.assert_true(not res_err["success"], "Detect Syntax Error (Missing ')')")
        self.assert_true("error" in res_err and res_err["error"]["type"] == "Syntax error", "Structured Error Object")
        self.assert_true("expected ')'" in res_err["user_message"], "Accurate Error Message")

        # Lexical error: unterminated string
        lexer_bad = "string msg = \"unterminated string literal;"
        res_lex = format_code(lexer_bad, language="c")
        self.assert_true(not res_lex["success"], "Detect Unterminated String Literal")
        self.assert_true(res_lex["error"]["type"] == "Lexical error", "Classified as Lexical Error")

        # Unsupported language
        res_unsupported = format_code("print('hi')", language="unknown_lang")
        self.assert_true(not res_unsupported["success"], "Reject Unsupported Language")
        self.assert_true(res_unsupported["error"]["type"] == "Unsupported language", "Unsupported Language Error Type")

    def test_performance_benchmarks(self):
        print("\n[SECTION 5: Latency and Performance Benchmarks]")

        sizes = {
            "Small (~5 lines)": "int x=1;\nif(x>0){\nprint(\"ok\");\n}\n",
            "Medium (~30 lines)": "\n".join([f"int v{i} = {i}; if(v{i}>0){{ print(\"{i}\"); }}" for i in range(15)]),
            "Large (~100 lines)": "\n".join([f"int item_{i} = {i * 2}; while(item_{i}>0){{ item_{i} = item_{i} - 1; }}" for i in range(50)])
        }

        print(f"  {'Sample Size':<22} | {'Iterations':<10} | {'Min (ms)':<10} | {'Avg (ms)':<10} | {'Max (ms)':<10}")
        print("  " + "-" * 70)

        for label, snippet in sizes.items():
            durations = []
            for _ in range(10):
                t0 = time.perf_counter()
                res = format_code(snippet, language="c")
                t1 = time.perf_counter()
                durations.append((t1 - t0) * 1000)

            min_d = min(durations)
            avg_d = sum(durations) / len(durations)
            max_d = max(durations)

            print(f"  {label:<22} | {len(durations):<10} | {min_d:<10.3f} | {avg_d:<10.3f} | {max_d:<10.3f}")
            self.assert_true(avg_d < 50.0, f"Performance Target ({label}) < 50ms (Actual: {avg_d:.2f}ms)")


if __name__ == "__main__":
    runner = BenchmarkRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
