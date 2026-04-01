#!/bin/bash
# 数据库自动备份脚本
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/var/www/engineering_system/backups
DB_PASS="V)|pi(ml:o+2s6}-@q<X"

# 导出数据库
export PGPASSWORD="$DB_PASS"
pg_dump -h localhost -U engineer -d engineering_db -F c -f $BACKUP_DIR/db_backup_$DATE.dump

# 删除7天前的备份
find $BACKUP_DIR -name "db_backup_*.dump" -mtime +7 -delete

# 记录备份日志
echo "[$(date)] Backup completed: db_backup_$DATE.dump" >> $BACKUP_DIR/backup.log
