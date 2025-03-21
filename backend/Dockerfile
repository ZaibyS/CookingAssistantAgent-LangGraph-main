# Use a Python base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/agents/
RUN pip install --no-cache-dir -r /app/agents/requirements.txt

# Copy the application code
COPY agents/cooking_assistant.py /app/agents/

# Copy the required files
COPY agents/logger.py /app/agents/
COPY agents/prompts.py /app/agents/
COPY .env /app/

# Install curl (for testing)
RUN apt-get update && apt-get install -y curl

# Set environment variables
ENV PYTHONPATH=/app/agents/
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Expose the API port
EXPOSE 8000

# Run the application and keep the container running
CMD ["bash", "-c", "python /app/agents/cooking_assistant.py && bash"]