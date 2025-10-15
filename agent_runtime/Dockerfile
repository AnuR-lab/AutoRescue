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
ENV GATEWAY_URL="https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
ENV BEDROCK_MODEL_ID="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
ENV COGNITO_CLIENT_ID="5ptprke4sq904kc6kv067d4mjo"
ENV COGNITO_CLIENT_SECRET="1k7ajt3pg59q2ef1oa9g449jteomhik63qod7e9vpckl0flnnp0r"
ENV COGNITO_DOMAIN="autorescue-1760552868.auth.us-east-1.amazoncognito.com"

# Expose port for AgentCore Runtime
EXPOSE 8080

# Run the agent
CMD ["python", "autorescue_agent.py"]
