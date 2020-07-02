FROM python:3.8-slim-buster

WORKDIR /app

# Install dependencies
RUN pip install python-telegram-bot matplotlib numpy pandas

# Copy the rest of source files
COPY . .

# Start point of the container
CMD ["python", "./bot.py"]