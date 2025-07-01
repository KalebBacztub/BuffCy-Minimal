# Use a more modern 32-bit version of Ubuntu with a compatible Python
FROM i386/ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && apt-get install -y \
    gdb \
    python3 \
    python3-pip \
    && apt-get clean

# Install the GDB MI library for Python
RUN pip3 install pygdbmi

# Declare an argument that we will get from docker-compose
ARG TARGET_BINARY

# Set up the working directory inside the container
WORKDIR /app

# Copy the specific binary we chose into the container
COPY targets/${TARGET_BINARY} ./${TARGET_BINARY}
# Copy the server and the entrypoint script
COPY gdb_mcp_server.py .
COPY entrypoint.sh .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose the GDB server port
EXPOSE 8080

# Set the entrypoint to our new script
ENTRYPOINT ["./entrypoint.sh"]