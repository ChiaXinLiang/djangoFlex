# Docker 網絡連接問題解決方案

## 1. 關鍵問題
- Docker 容器間的網絡通信需要在同一網絡中
- 容器內部使用服務名稱而不是 localhost 進行通信
- 需要正確配置環境變量以識別 Docker 環境

## 2. 解決步驟

### 2.1 Docker Compose 配置
```yaml
networks:
    djangoflex-network:    # 定義統一的網絡名稱
    driver: bridge

services:
    django:
        environment:
            - IS_DOCKER=True   # 標記 Docker 環境
            - NETWORK_NAME=djangoflex-network
        networks:
            - djangoflex-network
```

### 2.2 服務配置
```python
# settings/djangoFlex.py
IS_DOCKER = os.getenv('IS_DOCKER', 'False') == 'True'
NETWORK_NAME = os.getenv('NETWORK_NAME', 'djangoflex-network')
SRS_HOST = 'srs' if IS_DOCKER else 'localhost'  # 根據環境選擇主機名
```

### 2.3 URL 轉換邏輯
```python
# 在需要訪問其他服務的地方
if is_docker and 'localhost' in url:
    url = url.replace('localhost', 'srs')  # 使用容器服務名
```

## 3. 關鍵概念

### 3.1 Docker 網絡
- 使用 bridge 網絡實現容器間通信
- 容器可以通過服務名稱互相訪問
- 網絡隔離提供安全性

### 3.2 環境檢測
- 使用環境變量區分 Docker 環境
- 根據環境動態調整配置
- 保持代碼的靈活性

### 3.3 服務發現
- 使用服務名稱代替 IP 地址
- Docker DNS 自動解析服務名稱
- 支持容器的動態擴展

## 4. 驗證步驟

### 4.1 檢查網絡配置
```bash
# 列出所有 Docker 網絡
docker network ls

# 檢查特定網絡的詳細信息
docker network inspect djangoflex-network
```

### 4.2 測試容器間通信
```bash
# 測試容器間的網絡連接
docker exec -it django_container ping srs
```

### 4.3 檢查服務日誌
```bash
# 檢查 SRS 服務日誌
docker logs srs_container

# 檢查 Django 服務日誌
docker logs django_container
```

## 5. 最佳實踐

1. 統一網絡命名
   - 使用有意義的網絡名稱
   - 在所有配置中保持一致性

2. 使用環境變量
   - 通過環境變量控制行為
   - 避免硬編碼配置

3. 日誌記錄
   - 添加詳細的調試信息
   - 記錄關鍵操作和錯誤

4. 錯誤處理
   - 實現優雅的錯誤處理機制
   - 提供清晰的錯誤信息

5. 配置靈活性
   - 支持不同環境的配置
   - 保持代碼的可移植性

## 6. 注意事項

1. 網絡名稱
   - Docker Compose 會自動添加項目名稱作為前綴
   - 實際網絡名可能是 `project_name_network_name`

2. 服務名稱解析
   - 在容器內部使用服務名稱而不是 localhost
   - 確保服務名稱與 docker-compose.yml 中定義的一致

3. 環境變量
   - 在 Dockerfile 和 docker-compose.yml 中正確設置
   - 注意環境變量的優先級

4. 調試方法
   - 使用詳細的日誌輸出
   - 利用 Docker 的網絡調試工具