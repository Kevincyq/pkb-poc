#!/bin/bash

# PKB 当前部署环境备份脚本
# 用于在迁移前创建安全备份

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置
CURRENT_DIR=$(pwd)
BACKUP_DIR="/opt/pkb-backup-$(date +%Y%m%d-%H%M%S)"

echo "======================================"
echo "    PKB 环境备份脚本"
echo "======================================"
echo ""
log_info "当前目录: $CURRENT_DIR"
log_info "备份目录: $BACKUP_DIR"
echo ""

# 检查权限
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 root 权限运行: sudo $0"
    exit 1
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR"

log_info "开始备份当前 PKB 部署环境..."

# 1. 备份部署文件
log_info "备份部署文件..."
cp -r "$CURRENT_DIR" "$BACKUP_DIR/deployment_files"
log_success "部署文件备份完成"

# 2. 备份数据库
log_info "备份数据库..."
if docker ps | grep -q postgres; then
    POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep postgres | head -1)
    log_info "发现 PostgreSQL 容器: $POSTGRES_CONTAINER"
    
    # 尝试不同的备份方式
    if docker exec "$POSTGRES_CONTAINER" pg_dumpall -U postgres > "$BACKUP_DIR/database_full.sql" 2>/dev/null; then
        log_success "完整数据库备份成功"
    elif docker exec "$POSTGRES_CONTAINER" pg_dump -U pkb pkb > "$BACKUP_DIR/database_pkb.sql" 2>/dev/null; then
        log_success "PKB 数据库备份成功"
    else
        log_warning "自动数据库备份失败，请手动备份"
    fi
else
    log_warning "未发现 PostgreSQL 容器"
fi

# 3. 备份 Docker 信息
log_info "备份 Docker 环境信息..."
docker ps -a > "$BACKUP_DIR/docker_containers.txt"
docker images > "$BACKUP_DIR/docker_images.txt"
docker volume ls > "$BACKUP_DIR/docker_volumes.txt"
docker network ls > "$BACKUP_DIR/docker_networks.txt"

# 4. 备份系统信息
log_info "备份系统信息..."
echo "备份时间: $(date)" > "$BACKUP_DIR/backup_info.txt"
echo "备份目录: $CURRENT_DIR" >> "$BACKUP_DIR/backup_info.txt"
echo "系统信息: $(uname -a)" >> "$BACKUP_DIR/backup_info.txt"
echo "Docker 版本: $(docker --version)" >> "$BACKUP_DIR/backup_info.txt"

# 5. 创建恢复脚本
cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash
# PKB 环境恢复脚本

echo "PKB 环境恢复脚本"
echo "备份时间: $(cat backup_info.txt | grep "备份时间")"
echo ""

read -p "确认恢复到备份状态？这将覆盖当前部署 (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "恢复已取消"
    exit 0
fi

ORIGINAL_DIR=$(cat backup_info.txt | grep "备份目录" | cut -d: -f2 | xargs)

echo "停止当前服务..."
docker-compose down 2>/dev/null || true

echo "恢复部署文件..."
cp -r deployment_files/* "$ORIGINAL_DIR/"

echo "恢复数据库..."
if [ -f "database_full.sql" ]; then
    POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep postgres | head -1)
    if [ -n "$POSTGRES_CONTAINER" ]; then
        docker exec -i "$POSTGRES_CONTAINER" psql -U postgres < database_full.sql
        echo "数据库恢复完成"
    fi
elif [ -f "database_pkb.sql" ]; then
    POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep postgres | head -1)
    if [ -n "$POSTGRES_CONTAINER" ]; then
        docker exec -i "$POSTGRES_CONTAINER" psql -U pkb -d pkb < database_pkb.sql
        echo "PKB 数据库恢复完成"
    fi
fi

echo "启动服务..."
cd "$ORIGINAL_DIR"
docker-compose up -d

echo "恢复完成！"
EOF

chmod +x "$BACKUP_DIR/restore.sh"

# 6. 创建备份说明
cat > "$BACKUP_DIR/README.md" << EOF
# PKB 环境备份

## 备份信息
- 备份时间: $(date)
- 原始目录: $CURRENT_DIR
- 备份目录: $BACKUP_DIR

## 备份内容
- \`deployment_files/\`: 完整的部署文件和配置
- \`database_*.sql\`: 数据库备份文件
- \`docker_*.txt\`: Docker 环境信息
- \`backup_info.txt\`: 备份详细信息
- \`restore.sh\`: 自动恢复脚本

## 恢复方法

### 方法一：使用自动恢复脚本
\`\`\`bash
cd $BACKUP_DIR
sudo ./restore.sh
\`\`\`

### 方法二：手动恢复
1. 停止当前服务
   \`\`\`bash
   docker-compose down
   \`\`\`

2. 恢复文件
   \`\`\`bash
   cp -r $BACKUP_DIR/deployment_files/* $CURRENT_DIR/
   \`\`\`

3. 恢复数据库
   \`\`\`bash
   # 如果有完整备份
   docker exec -i postgres_container psql -U postgres < $BACKUP_DIR/database_full.sql
   
   # 或者 PKB 数据库备份
   docker exec -i postgres_container psql -U pkb -d pkb < $BACKUP_DIR/database_pkb.sql
   \`\`\`

4. 启动服务
   \`\`\`bash
   cd $CURRENT_DIR
   docker-compose up -d
   \`\`\`

## 注意事项
- 恢复前请确保停止所有相关服务
- 数据库恢复可能需要根据实际情况调整用户名和数据库名
- 如有问题，请参考 backup_info.txt 中的详细信息
EOF

log_success "🎉 备份完成！"
echo ""
echo "📁 备份位置: $BACKUP_DIR"
echo "📋 备份内容:"
echo "  • 部署文件: deployment_files/"
echo "  • 数据库备份: database_*.sql"
echo "  • Docker 信息: docker_*.txt"
echo "  • 恢复脚本: restore.sh"
echo "  • 说明文档: README.md"
echo ""
echo "🔄 恢复命令:"
echo "  cd $BACKUP_DIR && sudo ./restore.sh"
echo ""
log_info "现在可以安全地进行迁移了！"
