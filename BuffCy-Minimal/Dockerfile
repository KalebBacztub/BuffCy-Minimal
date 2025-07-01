# Use a 32-bit version of Ubuntu
FROM i386/ubuntu:16.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN dpkg --add-architecture i386
RUN apt-get update && apt-get install -y \
    gdb python3 python3-pip libc6:i386 && apt-get clean
RUN pip3 install pygdbmi

# --- This is the new part ---
# Declare an argument that we will get from docker-compose
ARG TARGET_BINARY=connmand_no_sec

# Set up the working directory
WORKDIR /app

# Copy the specific binary we chose into the container
COPY targets/${TARGET_BINARY} .

# Expose the GDB server port
EXPOSE 8080

# Run the GDB server with the chosen binary
CMD ["python3", "gdb_mcp_server.py", "./${TARGET_BINARY}"]