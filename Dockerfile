# Use the official Python image as base
FROM python:3.6

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Run the Python script when the container launches
CMD ["python", "TeraboxBot.py"]
