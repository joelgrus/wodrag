#!/bin/bash
# Create a database backup for deployment

echo "Creating database backup..."
docker exec wodrag_paradedb pg_dump -U postgres wodrag | gzip > data/wodrag_backup.sql.gz
echo "Backup saved to data/wodrag_backup.sql.gz"
echo "File size: $(du -h data/wodrag_backup.sql.gz | cut -f1)"