FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

# Set the command to run the entitlement service
CMD ["python", "entitlement/entitlement_service.py"]
