#!/bin/bash
set -e

# Runtime fix for writable output
mkdir -p /app/results
chmod -R 777 /app/results || true

# Start Streamlit server
exec streamlit run app.py --server.port=8080 --server.address=0.0.0.0
