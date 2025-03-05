# 翻译工作平台（Translation Management Platform）

## 项目简介
翻译工作平台是一个面向翻译任务的管理系统，支持项目创建、文件上传、内容翻译及翻译进度跟踪。通过本平台，用户可以高效地组织和管理多个翻译项目，并清晰地了解项目及文件的完成情况。

## 项目结构

- **backend/**：后端服务器，基于Node.js和Express，提供REST API。
  - `data/projects/`：存储项目数据和翻译文件。
  - `server.js`：服务器主文件，包含API路由和逻辑。

- **frontend-vue/**：前端界面，基于Vue.js开发，提供用户交互界面。
  - `src/`：包含Vue组件、路由和状态管理。
  - `public/index.html`：应用入口页面。

## 功能介绍

- **创建项目**：用户可创建新项目，提供项目名称和描述。
- **上传文件**：支持上传文本文件，自动分段，以便逐段翻译。
- **翻译管理**：每个文件的翻译内容可单独编辑、保存进度，系统实时计算并展示翻译完成率。
- **进度跟踪**：实时统计项目和文件的完成率。
- **下载翻译结果**：翻译完成后，可下载翻译后的完整文件。

## 安装与运行

### 后端（Backend）

进入backend目录并安装依赖：
```bash
cd backend
npm install
```
启动后端服务：
```bash
node server.js
```
后端服务运行于：http://localhost:3000

### 前端（Frontend）

进入frontend-vue目录并安装依赖：
```bash
cd frontend-vue
npm install
```
运行前端开发服务器：
```bash
npm run serve
```
访问前端：http://localhost:8080

## API接口

详细API接口包括项目管理、文件管理、翻译内容的获取和更新、文件上传与下载。

| 方法 | API路径 | 描述 |
|------|---------|------|
| GET | `/api/projects` | 获取所有项目 |
| POST | `/api/projects` | 创建新项目 |
| GET | `/api/projects/:id` | 获取特定项目详情 |
| PUT | `/api/projects/:id` | 更新项目信息 |
| DELETE | `/api/projects/:id` | 删除项目 |
| POST | `/api/projects/:projectId/files` | 上传文件到项目 |
| GET | `/api/projects/:projectId/files/:fileId` | 获取文件信息 |
| PUT | `/api/projects/:projectId/files/:fileId` | 更新文件翻译内容 |
| DELETE | `/api/projects/:projectId/files/:fileId` | 删除项目中的文件 |
| GET | `/api/projects/:projectId/files/:fileId/download` | 下载翻译后的文件 |

