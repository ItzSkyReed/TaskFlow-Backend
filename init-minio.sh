#!/bin/sh
set -e

until mc alias set local "http://${MINIO_HOST}:${MINIO_STORAGE_PORT}" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
    echo "MinIO не доступен, ожидание..."
    sleep 1
done

mc alias set local "http://${MINIO_HOST}:${MINIO_STORAGE_PORT}" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

if mc ls local/avatars >/dev/null 2>&1; then
    echo "Бакет avatars уже существует."
else
    echo "Создание бакета avatars..."
    mc mb local/avatars
fi

echo "Установка публичной политики на avatars..."
mc anonymous set public local/avatars

echo "Готово."