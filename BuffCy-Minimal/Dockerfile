FROM i386/ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential pkg-config libglib2.0-dev:i386 libdbus-1-dev:i386 \
    libreadline-dev:i386 libxtables-dev:i386 libgnutls28-dev:i386 gdb \
    python3 python3-pip dnsutils && apt-get clean

RUN pip3 install pygdbmi
ARG CFLAGS
ARG TARGET_BINARY

WORKDIR /build
COPY connman-1.34/ .
RUN make clean
RUN ./configure CFLAGS="${CFLAGS}"
RUN make

WORKDIR /app
RUN cp /build/src/connmand ./${TARGET_BINARY}

COPY gdb_mcp_server.py .
COPY exploit_trigger.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["./entrypoint.sh"]