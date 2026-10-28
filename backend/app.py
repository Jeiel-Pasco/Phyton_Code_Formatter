"""Flask REST API for Code Formatter Application.

Provides endpoints for formatting code, retrieving supported languages,
and system health checks with comprehensive validation, CORS support,
and structured error reporting.
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from backend.pipeline import format_code, SUPPORTED_LANGUAGES

# Serve frontend files from the frontend/ directory (resolved from project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
STATIC_DIR   = os.path.join(FRONTEND_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
# Enable CORS for frontend development
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 2MB maximum payload size
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

LANGUAGE_SAMPLES = {
    "c": (
        "// greet the user\n"
        "int x=10;string name = \"Ana\";\n"
        "if(x>5){print(\"big \"+name);}else{\n"
        "print(\"small\");}\n"
        "while(x>0){x=x-1;}"
    ),
    "cpp": (
        "// C++ sample demonstration\n"
        "#include <iostream>\n"
        "int count=5;string msg = \"Hello C++\";\n"
        "if(count>0){std::cout<<msg;}else{\n"
        "std::cout<<\"empty\";}\n"
        "while(count>0){count=count-1;}"
    ),
    "java": (
        "// Java calculation and logic\n"
        "int total=100;String user = \"Developer\";\n"
        "if(total>=100){System.out.println(user);}else{\n"
        "System.out.println(\"pending\");}\n"
        "for(int i=0;i<5;i++){total=total+i;}"
    ),
    "javascript": (
        "// JavaScript greeting routine\n"
        "let x=10;const name = \"Ana\";\n"
        "if(x>5){console.log(\"big \"+name);}else{\n"
        "console.log(\"small\");}\n"
        "while(x>0){x=x-1;}"
    ),
    "python": (
        "# Python greeting routine\n"
        "x = 10\n"
        "name = \"Ana\"\n"
        "if x > 5:\n"
        "    print(\"big \" + name)\n"
        "else:\n"
        "    print(\"small\")\n"
        "while x > 0:\n"
        "    x = x - 1"
    )
}

LANGUAGE_DETAILS = [
    {"id": "c", "name": "C", "extension": ".c", "sample": LANGUAGE_SAMPLES["c"]},
    {"id": "cpp", "name": "C++", "extension": ".cpp", "sample": LANGUAGE_SAMPLES["cpp"]},
    {"id": "java", "name": "Java", "extension": ".java", "sample": LANGUAGE_SAMPLES["java"]},
    {"id": "javascript", "name": "JavaScript", "extension": ".js", "sample": LANGUAGE_SAMPLES["javascript"]},
    {"id": "python", "name": "Python", "extension": ".py", "sample": LANGUAGE_SAMPLES["python"]},
]


@app.route("/", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def serve_frontend():
    """Serve the React frontend application."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """System health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Code Formatter API",
        "version": "1.0.0"
    }), 200


@app.route("/api/languages", methods=["GET"])
def get_languages():
    """Return list of supported programming languages and metadata."""
    return jsonify({
        "languages": LANGUAGE_DETAILS
    }), 200


@app.route("/api/format", methods=["POST"])
def format_endpoint():
    """Format submitted source code through the compiler pipeline."""
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": {
                "type": "InvalidInput",
                "message": "Request payload must be valid JSON with 'Content-Type: application/json'."
            },
            "user_message": "Invalid request: Payload must be JSON."
        }), 400

    data = request.get_json()
    code = data.get("code", "")
    language = data.get("language", "c")
    indent_size = int(data.get("indent_size", 4))
    indent_style = str(data.get("indent_style", "spaces")).lower()
    max_line_length = int(data.get("max_line_length", 80))

    # Clamp indentation parameters safely
    if indent_size < 1 or indent_size > 8:
        indent_size = 4
    if indent_style not in ("spaces", "tabs"):
        indent_style = "spaces"
    if max_line_length < 20 or max_line_length > 200:
        max_line_length = 80

    result = format_code(
        code=code,
        language=language,
        indent_size=indent_size,
        indent_style=indent_style,
        max_line_length=max_line_length
    )

    status_code = 200 if result.get("success", False) else 400
    return jsonify(result), status_code


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "success": False,
        "error": {
            "type": "PayloadTooLarge",
            "message": "Submitted code exceeds maximum size limit (2MB)."
        },
        "user_message": "File too large: maximum code size is 2MB."
    }), 413


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": {
            "type": "InternalServerError",
            "message": "An unexpected server error occurred."
        },
        "user_message": "Server error encountered while processing code."
    }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
