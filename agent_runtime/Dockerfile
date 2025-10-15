FROM public.ecr.aws/docker/library/python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY autorescue_agent.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GATEWAY_URL=""
ENV ACCESS_TOKEN=""
ENV BEDROCK_MODEL_ID="us.anthropic.claude-3-5-sonnet-20241022-v2:0"

# Expose port for AgentCore Runtime
EXPOSE 8080

# Run the agent
CMD ["python", "autorescue_agent.py"]
