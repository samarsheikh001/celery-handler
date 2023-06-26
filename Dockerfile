FROM pytorch/pytorch:latest

WORKDIR /app

RUN mkdir -p ~/.huggingface
# Use the environment variable to write the token to the file
RUN echo -n $HUGGINGFACE_TOKEN > ~/.huggingface/token

# Update system and install necessary system packages for git and wget
RUN apt-get update && apt-get install -y git wget && rm -rf /var/lib/apt/lists/*

# Clone the repository
RUN git clone https://github.com/samarsheikh001/celery-handler.git .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable
ENV PYTHONUNBUFFERED 1

# Make the shell script executable
RUN chmod +x run.sh

# Run celery worker when the container launches
CMD ["celery", "-A", "make_celery", "worker", "--loglevel", "INFO", "-c", "1"]