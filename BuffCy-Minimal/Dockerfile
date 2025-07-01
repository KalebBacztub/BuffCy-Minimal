# Use a 32-bit version of Ubuntu
FROM i386/ubuntu:16.04

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Update and install 32-bit dependencies
RUN dpkg --add-architecture i386
RUN apt-get update && apt-get install -y \
    gdb \
    python3 \
    python3-pip \
    libc6:i386 \
    && apt-get clean

# Install the GDB MI library for Python
RUN pip3 install pygdbmi

# Set up the working directory inside the container
WORKDIR /app

# Copy the server and the vulnerable binary into the container
COPY gdb_mcp_server.py .
COPY target/connmand .

# Expose the port for the GDB server to listen on
EXPOSE 8080

# This command will be run when the container starts
CMD ["python3", "gdb_mcp_server.py", "./connmand"]