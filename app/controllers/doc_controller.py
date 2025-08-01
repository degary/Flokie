"""
API Documentation Controller Module

This module provides the API documentation endpoint using Flask-RESTX.
"""

import logging

from flask import Blueprint, current_app, jsonify, render_template_string

from app.extensions import api

logger = logging.getLogger(__name__)

# Create documentation blueprint
doc_bp = Blueprint("doc", __name__, url_prefix="/api/doc")

# Swagger UI HTML template
SWAGGER_UI_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Flask API Template - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/api/swagger.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            });
        };
    </script>
</body>
</html>
"""


@doc_bp.route("/")
def api_documentation():
    """
    Serve the API documentation using Swagger UI.

    Returns:
        str: HTML page with Swagger UI
    """
    logger.info("API documentation requested")
    return render_template_string(SWAGGER_UI_TEMPLATE)


@doc_bp.route("")
def api_documentation_no_slash():
    """
    Serve the API documentation using Swagger UI (without trailing slash).

    Returns:
        str: HTML page with Swagger UI
    """
    logger.info("API documentation requested (no slash)")
    return render_template_string(SWAGGER_UI_TEMPLATE)


# Create a separate blueprint for swagger.json to avoid conflicts
swagger_bp = Blueprint("swagger", __name__, url_prefix="/api")


@swagger_bp.route("/swagger.json")
def swagger_json():
    """
    Serve the OpenAPI/Swagger JSON specification.

    Returns:
        dict: OpenAPI specification in JSON format
    """
    logger.info("Swagger JSON specification requested")
    return jsonify(api.__schema__)
