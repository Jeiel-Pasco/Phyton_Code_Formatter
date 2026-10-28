# Code Formatter — Full-Stack Web Application

A modern, responsive, developer-grade Code Formatter and Beautifier built with **React.js & Vite** on the frontend and a **Python & Flask compiler pipeline** on the backend.

The system implements a true code formatting pipeline using **lexical analysis (`lexer.py`)**, **AST syntax parsing (`parser.py`)**, **formatting rules & pretty printing (`printer.py`)**, and structured JSON error reporting (`errors.py`), preserving comments, string literals, and semantic integrity.

---

## 🏗️ Architecture & Module Workflow

```text
USER / Browser
      │
      ▼
React Frontend (App.jsx + styles.css)
      │
      │  HTTP POST /api/format (via Vite proxy :5173 -> :5000)
      ▼
Flask API Server (backend/app.py)
      │
      ▼
Central Pipeline (backend/pipeline.py)
      │
      ├──> Lexical Analyzer (backend/lexer.py)
      │       Converts source code into typed Tokens with line/column tracking.
      │
      ├──> Syntax Parser (backend/parser.py)
      │       Builds an AST/IR, validates grammar, preserves comments as AST nodes.
      │
      └──> Pretty Printer (backend/printer.py)
              Applies indentation, operator spacing, brace formatting, and blank lines.
      │
      ▼
Flask JSON Response (Execution metrics, formatted code, or structured error)
      │
      ▼
React Output Editor & Pipeline Status Bar
```

---

## 📁 Project Structure

```text
code-formatter/
│
├── frontend/
│   ├── App.jsx            # Main React UI inspired by VS Code and developer tools
│   ├── styles.css         # Modern dark/light responsive layout & gutter styling
│   ├── vite.config.js     # Vite configuration with Flask API reverse proxy
│   ├── index.html         # Application HTML entry point
│   └── package.json       # React & Vite dependency manifest
│
├── backend/
│   ├── lexer.py           # Multi-language lexical analyzer & token generator
│   ├── errors.py          # Centralized structured exception hierarchy
│   ├── parser.py          # AST parser recognizing blocks, control flow, & statements
│   ├── printer.py         # Code formatter applying indentation & spacing rules
│   ├── pipeline.py        # Pipeline coordinator and metrics collector
│   └── app.py             # Flask REST API endpoints (/api/format, /api/languages, /api/health)
│
├── Tests/
│   └── benchmark.py       # Automated test suite and latency benchmark runner
│
├── requirements.txt       # Python backend dependencies (Flask, Flask-CORS)
└── README.md              # Project documentation and developer guide
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: 3.9+ (Installed: Python 3.14)
- **Node.js**: 18+ (Installed: Node.js v24)
- **npm**: 9+

### 2. Backend Setup & Startup
Install backend dependencies and run the Flask API server:

```powershell
# Navigate to the project root
cd E:\CodeFormatter

# Install Python requirements
python -m pip install -r requirements.txt

# Start the Flask backend server (port 5000)
python backend/app.py
```

The Flask server will start at `http://127.0.0.1:5000`.

### 3. Frontend Setup & Startup
In a separate terminal:

```powershell
# Navigate to the frontend directory
cd E:\CodeFormatter\frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 🧪 Running Automated Tests and Benchmarks

The automated benchmark suite evaluates:
- **Formatting correctness**: Indentation, operator spacing, brace placement, nested blocks
- **Preservation**: Exact preservation of comments and string literals
- **Idempotency**: `format(format(code)) == format(code)`
- **Error handling**: Unterminated strings, mismatched braces, missing tokens, unsupported languages
- **Performance**: Execution latencies across small (~5 lines), medium (~30 lines), and large (~100 lines) codebases

Run the benchmark suite:
```powershell
python Tests/benchmark.py
```

Expected result:
```text
======================================================================
          CODE FORMATTER AUTOMATED TEST & BENCHMARK SUITE          
======================================================================
[SECTION 1: Formatting Correctness & Comment Preservation] -> 8/8 PASS
[SECTION 2: Multi-Language Syntax Support]               -> 8/8 PASS
[SECTION 3: Idempotency & Whitespace Stability]          -> 3/3 PASS
[SECTION 4: Robust Error Handling]                       -> 8/8 PASS
[SECTION 5: Latency and Performance Benchmarks]          -> 5/5 PASS
======================================================================
  Total Passed: 32 / 32 (100% Success Rate)
======================================================================
```

---

## 🌐 API Reference

### `POST /api/format`
Formats source code using the compiler pipeline.

#### Request Example:
```json
{
  "code": "// greet the user\nint x=10;string name = \"Ana\";\nif(x>5){print(\"big \"+name);}else{\nprint(\"small\");}\nwhile(x>0){x=x-1;}",
  "language": "c",
  "indent_size": 4,
  "indent_style": "spaces",
  "max_line_length": 80
}
```

#### Success Response (`200 OK`):
```json
{
  "success": true,
  "formatted_code": "// greet the user\nint x = 10;\nstring name = \"Ana\";\n\nif (x > 5) {\n    print(\"big \" + name);\n} else {\n    print(\"small\");\n}\n\nwhile (x > 0) {\n    x = x - 1;\n}\n",
  "language": "c",
  "execution_time_ms": 0.18,
  "original_lines": 5,
  "formatted_lines": 14,
  "comments_preserved": 1,
  "lexer_status": "OK",
  "parser_status": "OK",
  "indent_size": 4,
  "indent_style": "spaces",
  "max_line": 80
}
```

#### Error Response (`400 Bad Request`):
```json
{
  "success": false,
  "error": {
    "type": "Syntax error",
    "message": "expected ')' but found '{'",
    "line": 3,
    "column": 14,
    "suggestion": "Fix the source and format again."
  },
  "user_message": "Syntax error at line 3, column 14: expected ')' but found '{'. Fix the source and format again.",
  "execution_time_ms": 0.12
}
```

### `GET /api/languages`
Returns the list of supported programming languages and default sample snippets.

### `GET /api/health`
Returns the health status and version of the API service.

---

## 🎨 Frontend Features

- **Side-by-Side Dual Panels**: Synchronized line numbers and independent/synced scrolling.
- **Python-only scope**: The interface targets Python (fixed 4-space indentation); the language, indent, and sample selectors were removed.
- **Interactive Controls**:
  - `Format` (Ctrl+Enter): Prominent amber action button.
  - `Download`: Downloads formatted code with the `.py` file extension.
  - `Paste` & `Copy`: Instant clipboard access with animated toast indicators.
  - `Clear` (Ctrl+K): One-click canvas reset.
- **Pipeline Status Bar**: Real-time badges for Lexer status, Parser status, comment counts, indentation, line count comparison, and execution time in milliseconds.
- **Mockup-Accurate Error Banner**: Dedicated error alert with line/column location, error type, and actionable suggestions.
- **Dark & Light Mode**: Seamless theme toggle with persistent developer styling.
