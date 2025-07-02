# Use a more modern 32-bit version of Ubuntu
FROM i386/ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install all necessary dependencies
RUN apt-get update && apt-get install -y \
    build-essential pkg-config libglib2.0-dev:i386 libdbus-1-dev:i386 \
    libreadline-dev:i386 libxtables-dev:i386 libgnutls28-dev:i386 gdb \
    python3 python3-pip dnsutils && apt-get clean

RUN pip3 install pygdbmi

# Add build-time arguments for compilation flags
ARG CFLAGS
ARG TARGET_BINARY

# Copy and compile the connman source code
WORKDIR /build
COPY connman-1.34/ .
RUN make clean
RUN ./configure CFLAGS="${CFLAGS}" --prefix=/usr --sysconfdir=/etc --localstatedir=/var
RUN make

# Set up the final runtime environment
WORKDIR /app
RUN cp /build/src/connmand ./${TARGET_BINARY}

COPY gdb_mcp_server.py .
COPY exploit_trigger.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["./entrypoint.sh"]