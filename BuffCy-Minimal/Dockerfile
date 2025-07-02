# Use a more modern 32-bit version of Ubuntu
FROM i386/ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies, including dnsutils
RUN apt-get update && apt-get install -y \
    gdb \
    python3 \
    python3-pip \
    dnsutils \
    && apt-get clean

# Install the GDB MI library for Python
RUN pip3 install pygdbmi

# Declare an argument that we will get from docker-compose
ARG TARGET_BINARY

# Set up the working directory inside the container
WORKDIR /app

# Copy the necessary files into the container
COPY targets/${TARGET_BINARY} ./${TARGET_BINARY}
COPY gdb_mcp_server.py .
COPY dns_spoofer.py .  # <-- ADD THIS LINE
COPY entrypoint.sh .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose the GDB server port
EXPOSE 8080

# Set the entrypoint to our new script
ENTRYPOINT ["./entrypoint.sh"]