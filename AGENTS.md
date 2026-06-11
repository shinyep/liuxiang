# AGENTS.md

## 项目概览

这是一个“成品追溯与客户管理系统”。后端使用 Django 5 / Django REST Framework，数据库使用 SQLite；前端使用 Vue 3 + Vue CLI，主要通过 Axios 调用 `/api/v1/` 接口。项目还包含一个 `tkinter` 桌面启动器，用于启动 Django 服务并打开浏览器访问系统。

## 目录说明

- `flow_system/api/`: Django 业务应用，包含模型、序列化器、视图、路由、迁移和导入/清理数据的 management commands。
- `flow_system/flow_system/`: Django 项目配置，包含 `settings.py`、`urls.py`、`wsgi.py`、`asgi.py`。
- `flow_system/launcher_gui.py`: Windows 桌面启动器，默认启动 Django 服务到 `http://localhost:8002/`，并包含应用版本日志。
- `flow_frontend/`: 当前更活跃的 Vue 前端源码目录。这里的 `package.json` 版本为 `0.5.0`，`ShipmentTracking.vue`、`StatisticsDashboard.vue` 等文件更新较新。
- `flow_system/flow_frontend/`: 打包/历史用的前端副本，版本为 `0.1.0`。修改前端功能时优先检查 `flow_frontend/`，如需打包再确认是否要同步到这里。
- `flow_system/data/`: 开发运行时 SQLite 数据目录，通常包含 `db.sqlite3`。
- `flow_system/backups/`、`数据库备份/`: 数据库备份目录。不要随意覆盖或删除。
- `build/`、`dist/`、`venv/`、`node_modules/`、`__pycache__/`: 生成物或依赖目录，通常不要手工编辑。

## 常用命令

后端依赖安装：

```powershell
.\venv\Scripts\pip.exe install -r requirements.txt
```

启动桌面启动器和后端服务：

```powershell
.\venv\Scripts\python.exe flow_system\launcher_gui.py
```

无 GUI 方式检查 Django 配置：

```powershell
$env:PYTHONPATH = "$PWD\flow_system\flow_system;$PWD\flow_system"
$env:DJANGO_SETTINGS_MODULE = "settings"
.\venv\Scripts\python.exe -m django check
```

运行 Django 测试：

```powershell
$env:PYTHONPATH = "$PWD\flow_system\flow_system;$PWD\flow_system"
$env:DJANGO_SETTINGS_MODULE = "settings"
.\venv\Scripts\python.exe -m django test api
```

前端开发服务：

```powershell
cd flow_frontend
npm install
npm run serve
```

前端构建：

```powershell
cd flow_frontend
npm run build
```

前端开发服务默认使用 `8082` 端口，并把 `/api` 代理到 `http://localhost:8002`。

## 数据和业务注意事项

- 主要业务模型是 `Customer`、`Shipment`、`ProductionTimeSlot`。
- `Shipment` 与 `Customer` 是外键关系，`ProductionTimeSlot` 与 `Shipment` 是外键关系。
- `ShipmentViewSet.create()` 会在没有 `customer_id` 但提供 `area_code` 时自动查找或创建客户。
- POST 新增流向记录时，如果关键字段匹配已有记录，会追加新的生产时间段；PUT/PATCH 更新时，序列化器会用新时间段替换旧时间段。
- 统计接口通常把 `specification` 转成数字，并乘以有效生产时间段数量；`start_time_str` 为空或等于 `F` 的时间段不计入有效数量。
- Excel 导入逻辑依赖列顺序和日期/时间格式。改动导入字段时，要同步检查 API 导入视图和 management command。
- 数据库导入接口会替换当前 SQLite 文件。任何涉及数据库覆盖、清空、恢复的改动都要先确认备份路径和用户意图。

## 编码和文本

- 项目里部分中文注释或字符串已经出现 mojibake（乱码形态）。除非任务明确要求修复编码，不要批量重写这些文件，以免引入大面积无关 diff。
- 新增业务文案优先使用清晰中文；修改既有文案时尽量保持周边风格。
- 不要把客户资料、数据库备份、Excel 原始业务数据当作临时测试素材随意改写。

## 开发约定

- 优先保持现有 Django/DRF 和 Vue Options API 写法，不为小改动引入新框架或大规模重构。
- 后端接口路径集中在 `flow_system/api/urls.py`，项目根路由在 `flow_system/flow_system/urls.py`。
- 前端 API 调用主要在 Vue 组件内，改接口字段时同步检查提交表单、列表展示、统计页和导入/导出逻辑。
- 对数据模型做字段变更时，必须同步更新 serializer、view、migration、前端字段映射和 Excel 导入逻辑。
- 保持生成目录不参与源码改动；需要打包时再处理 `dist/`、`build/` 和 PyInstaller spec。
- 当前项目根目录不是 Git 仓库；`flow_frontend/` 内部有单独的 `.git`。执行 Git 命令前先确认所在目录。

## 验证建议

- 后端改动后至少运行 `django check`；涉及模型、serializer、view 时运行 `django test api`。
- 前端改动后运行 `npm run lint` 和 `npm run build`。
- 涉及前后端交互时，同时启动后端 `8002` 和前端 `8082`，手动验证新增、编辑、导入、统计等关键路径。
- 涉及数据库导入、备份、清空或 Excel 导入时，先复制一份 SQLite 或使用测试数据库验证。
