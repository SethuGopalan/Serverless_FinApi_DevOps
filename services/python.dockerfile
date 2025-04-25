
FROM python:3.11-slim

WORKDIR /app

# Copy FastAPI app and requirements
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Set default handler via environment variable if needed
ARG HANDLER=api.py
ENV HANDLER=${HANDLER}

# Run the FastAPI app
ENTRYPOINT ["python", "-u", "api.py"]

