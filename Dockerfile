FROM python:3.12 as base
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN poetry install --no-root
CMD ["poetry", "run", "/app/main.py"]