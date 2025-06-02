#!/bin/bash
set -e

# Konfigurasi
MAX_RETRIES=30
RETRY_INTERVAL=2
POSTGRES_HOST=db   # Nama service db sesuai docker-compose.yml
POSTGRES_PORT=5432 # Port default PostgreSQL

# Fungsi untuk menunggu PostgreSQL siap
wait_for_postgres() {
    echo "Menunggu PostgreSQL siap..."
    local retry_count=0
    
    while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
        retry_count=$((retry_count + 1))
        
        if [ $retry_count -ge $MAX_RETRIES ]; then
            echo "Error: Gagal menghubungi PostgreSQL setelah $MAX_RETRIES percobaan"
            exit 1
        fi
        
        echo "Percobaan $retry_count/$MAX_RETRIES: PostgreSQL tidak tersedia - menunggu ${RETRY_INTERVAL}s"
        sleep $RETRY_INTERVAL
    done
    
    echo "PostgreSQL sudah siap!"
}

# Fungsi utama untuk menjalankan aplikasi Django
main() {
    # Tunggu PostgreSQL siap
    wait_for_postgres

    # Jalankan migrations Django
    echo "Menjalankan migrasi Django..."
    python /app/userreg/manage.py migrate

    # Mulai server Django
    echo "Menjalankan aplikasi Django..."
    exec python /app/userreg/manage.py runserver 0.0.0.0:8000
}

main "$@"
