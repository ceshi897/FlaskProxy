# Overview

This is a Flask-based HTTP proxy server that forwards all incoming requests to a specific target API endpoint (`https://webapi.360se.dpdns.org`). The application acts as a transparent proxy, maintaining request methods, headers, query parameters, and request bodies while routing traffic to the target server. It's designed to handle all HTTP methods (GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD) and preserve the original request structure.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Design Pattern
The application follows a simple proxy pattern with a single Flask route that captures all incoming requests and forwards them to a predefined target URL. This design provides a lightweight solution for API proxying without complex routing logic.

## Request Handling Architecture
- **Universal Route Handler**: A single Flask route with catch-all path matching (`/<path:path>`) handles all HTTP methods
- **Header Filtering**: Implements a blacklist approach to exclude connection-specific headers that could cause proxy issues
- **URL Construction**: Uses `urljoin` to properly construct target URLs while preserving query parameters
- **Host Header Override**: Explicitly sets the Host header to match the target server's expected value

## Error Handling and Logging
- **Debug Logging**: Comprehensive logging system for request tracking and debugging
- **Exception Handling**: The proxy function is wrapped in try-catch logic (implementation appears incomplete in the provided code)

## Configuration Management
- **Environment-based Secrets**: Uses environment variables for sensitive configuration like session secrets
- **Hardcoded Target**: The target URL is hardcoded, making this a single-purpose proxy

## Deployment Structure
- **Entry Point Separation**: `main.py` serves as the application entry point, importing the Flask app from `app.py`
- **Development Configuration**: Configured for development with debug mode enabled and accessible on all interfaces

# External Dependencies

## Core Framework
- **Flask**: Web framework for handling HTTP requests and responses
- **Requests**: HTTP library for making outbound requests to the target API

## Target Integration
- **360se Web API**: The proxy forwards all traffic to `https://webapi.360se.dpdns.org`
- **DNS Dependency**: Relies on the dpdns.org domain resolution for the target service

## Runtime Environment
- **Python Standard Library**: Uses `os`, `logging`, and `urllib.parse` for core functionality
- **Environment Variables**: Depends on optional `SESSION_SECRET` environment variable for Flask session management