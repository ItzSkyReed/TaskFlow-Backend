FROM quay.io/minio/minio:latest

RUN curl -sSL https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc \
    && chmod +x /usr/local/bin/mc

COPY init-minio.sh /usr/bin/init-minio.sh
RUN chmod +x /usr/bin/init-minio.sh

ENTRYPOINT ["/usr/bin/init-minio.sh"]