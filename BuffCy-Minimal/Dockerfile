FROM i386/ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# FIX: Add 'iproute2' and 'netcat-traditional' to the installation list
RUN apt-get update && apt-get install -y \
    build-essential pkg-config libglib2.0-dev:i386 libdbus-1-dev:i386 \
    libreadline-dev:i386 libxtables-dev:i386 libgnutls28-dev:i386 gdb \
    python3 python3-pip dnsutils dbus iproute2 netcat-traditional && apt-get clean

RUN pip3 install pygdbmi
ARG CFLAGS
ARG TARGET_BINARY

WORKDIR /build
COPY connman-1.34/ .
RUN make clean
# The --sysconfdir=/etc flag tells connman where to look for config files
RUN ./configure CFLAGS="${CFLAGS}" --prefix=/usr --sysconfdir=/etc --localstatedir=/var
RUN make
RUN make install

WORKDIR /app
RUN cp /build/src/connmand ./${TARGET_BINARY}

COPY gdb_mcp_server.py .
COPY target_entrypoint.sh .

# --- ADD CONNMAN CONFIGURATION ---
RUN mkdir -p /etc/connman
COPY main.conf /etc/connman/main.conf

ENTRYPOINT ["./target_entrypoint.sh"]