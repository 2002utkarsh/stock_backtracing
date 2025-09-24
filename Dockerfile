# --- Stage 1: The C++ Builder ---
FROM gcc:latest AS builder
WORKDIR /usr/src/app/cpp_engine
COPY cpp_engine/ .
RUN g++ -shared -fPIC -o libbacktester.so backtester.cpp

# --- Stage 2: The Python Runner ---
FROM python:3.9
WORKDIR /app

# --- THIS IS THE KEY CHANGE ---
# Copy the compiled library DIRECTLY into the python_app folder.
COPY --from=builder /usr/src/app/cpp_engine/backtester.dll ./python_app/

# Copy the rest of the Python app.
COPY python_app/ ./python_app/

# We no longer need to copy the /data folder for main.py, but it's needed for notifier.py
COPY data/ ./data/ 

# Set the new working directory to where our script is.
WORKDIR /app/python_app

# Install dependencies from the requirements file now located in this directory.
RUN pip install --no-cache-dir -r requirements.txt

# This command runs from the new WORKDIR (/app/python_app)
CMD ["python", "main.py"]