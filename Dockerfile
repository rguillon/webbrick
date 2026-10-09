# The game is static files (index.html + the Python modules it fetches into
# Pyodide), so the standard library's http.server is all it needs.
FROM python:3.12-slim

WORKDIR /app

# URLs mirror repo paths: the page is /index.html, the modules /src/webbrick/*.py
COPY index.html /app/index.html
COPY src/webbrick/ /app/src/webbrick/

EXPOSE 8000

# Bind to all interfaces so the server is reachable through the published port
CMD ["python", "-m", "http.server", "8000", "--bind", "0.0.0.0", "--directory", "/app"]
