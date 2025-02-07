# Use the slim Python 3.12 image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install system dependencies: libpq-dev provides the libpq library required by psycopg
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy the entire project into the container (build context should be the project root)
COPY . .

# Install Python dependencies from requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Set the command to run the data service
CMD ["python", "data/data_service.py"]
