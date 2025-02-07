# Use Python slim image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy everything into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the controller service
CMD ["python", "controller/controller.py"]
