# AMap 高德地图 Skill

通过脚本直连高德 Web Service API 完成地理编码、逆地理编码、IP 定位、天气、路径规划、距离测量和 POI 查询。

## 前置准备

1. 配置高德地图 API Key：
```bash
export AMAP_MAPS_API_KEY="你的API密钥"
```

2. 安装 Bun（如果还没有）：
```bash
curl -fsSL https://bun.sh/install | bash
```

## 快速开始

在 skill 目录下运行：

```bash
cd /path/to/amap
bun scripts/amap.ts --help
```

## 可用命令

### 地理编码/逆地理编码

**地理编码（地址 → 坐标）**：
```bash
bun scripts/amap.ts geocode --address "北京市朝阳区阜通东大街6号" --city 北京
```

**逆地理编码（坐标 → 地址）**：
```bash
bun scripts/amap.ts reverse-geocode --location 116.481488,39.990464
```

### 路径规划

**驾车路线（地址）**：
```bash
bun scripts/amap.ts drive-route-address \
  --origin-address "瘦西湖" \
  --destination-address "三盛国际广场" \
  --origin-city 扬州 --destination-city 扬州
```

**驾车路线（坐标）**：
```bash
bun scripts/amap.ts drive-route-coords \
  --origin 119.418306,32.416068 \
  --destination 119.397678,32.380922
```

**步行路线**：
```bash
bun scripts/amap.ts walk-route-address \
  --origin-address "起点地址" \
  --destination-address "终点地址" \
  --origin-city 城市 --destination-city 城市
```

**骑行路线**：
```bash
bun scripts/amap.ts bike-route-address \
  --origin-address "起点地址" \
  --destination-address "终点地址" \
  --origin-city 城市 --destination-city 城市
```

**公交路线**：
```bash
bun scripts/amap.ts transit-route-address \
  --origin-address "起点地址" \
  --destination-address "终点地址" \
  --origin-city 城市 --destination-city 城市
```

### POI 搜索

**关键词搜索**：
```bash
bun scripts/amap.ts poi-text --keywords "咖啡" --city 北京 --citylimit true
```

**周边搜索**：
```bash
bun scripts/amap.ts poi-around \
  --location 116.481488,39.990464 \
  --radius 1000 \
  --keywords "餐厅"
```

### 其他

**天气查询**：
```bash
bun scripts/amap.ts weather --city 北京 --extensions base
```

**IP 定位**：
```bash
bun scripts/amap.ts ip-location --ip 114.114.114.114
```

**距离测量**：
```bash
bun scripts/amap.ts distance \
  --origins 116.481488,39.990464\|116.434307,39.90909 \
  --destination 116.315613,39.998935 \
  --type 1
```

## 命令映射表

完整命令列表请参考：[references/command-map.md](references/command-map.md)

使用示例请参考：[references/examples.md](references/examples.md)

## 直接调用 API（无需 Bun）

如果没有安装 Bun，也可以直接用 curl 调用高德 API：

```bash
# 地理编码
curl "https://restapi.amap.com/v3/geocode/geo?key=你的API密钥&address=瘦西湖&city=扬州"

# 驾车路线规划
curl "https://restapi.amap.com/v3/direction/driving?key=你的API密钥&origin=119.418306,32.416068&destination=119.397678,32.380922"
```

## 相关资源

- **高德地图开放平台**: https://lbs.amap.com/
- **Web服务 API 文档**: https://lbs.amap.com/api/webservice/summary
