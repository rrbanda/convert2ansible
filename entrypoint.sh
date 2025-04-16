#!/bin/bash
set -e

# Runtime permission fix for OpenShift
mkdir -p /app/results
chmod -R 777 /app/results || true

# Start Streamlit
exec streamlit run app.py --server.port=8080 --server.address=0.0.0.0
