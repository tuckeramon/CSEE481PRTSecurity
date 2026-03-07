FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080

# TODO: Modify app.py to add your PRT dashboard
# See README.md for examples

CMD ["python", "app.py"]