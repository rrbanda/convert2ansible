FROM registry.access.redhat.com/ubi9/python-311

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/results && chmod -R 777 /app/results

EXPOSE 8080

ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLECORS=false

USER 1001

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
