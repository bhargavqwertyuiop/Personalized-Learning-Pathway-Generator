# syntax=docker/dockerfile:1
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container's working directory
COPY requirements.txt ./

# Install the Python dependencies
# The --no-cache-dir flag is a best practice for smaller, more efficient images
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application when the container starts
CMD ["python3", "app.py"]
