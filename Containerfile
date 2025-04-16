# Use UBI as base image
FROM registry.access.redhat.com/ubi9/python-311

# Set working directory
WORKDIR /app

# Copy requirements (you can generate this with `pip freeze > requirements.txt`)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Set environment for Streamlit to run non-interactively
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLECORS=false

# OpenShift compatible user
USER 1001

# Run the app
CMD ["streamlit", "run", "app.py"]
