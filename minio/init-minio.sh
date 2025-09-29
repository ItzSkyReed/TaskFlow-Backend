#!/bin/sh
set -e

# Запускаем MinIO в фоне
/usr/bin/minio server /data --console-address ":${MINIO_WEB_PORT}" --address ":${MINIO_STORAGE_PORT}" &

# Ждём, пока MinIO поднимется
echo "Ожидание запуска MinIO..."
until curl -f http://localhost:"${MINIO_WEB_PORT}"/minio/health/live >/dev/null 2>&1; do
    echo "MinIO не доступен, ожидание..."
    sleep 1
done

# Настройка mc
mc alias set local "http://localhost:${MINIO_STORAGE_PORT}" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

# Создание бакета, если его нет
if mc ls local/avatars >/dev/null 2>&1; then
    echo "Бакет avatars уже существует."
else
    echo "Создание бакета avatars..."
    mc mb local/avatars
fi

# Делаем бакет публичным
mc anonymous set public local/avatars

echo "Инициализация завершена."

# Держим контейнер живым
wait -n