# Auto-Translate 项目

这是一个 Web 应用程序，旨在管理项目和相关文件，并可能提供自动翻译功能。它包含一个 Python Flask 后端和一个 Vue.js 前端。

## 功能特性

* **项目管理:** 创建、查看和管理项目。
* **文件管理:** 在项目中上传、查看和管理文件。
* **（可能）翻译功能:** （根据项目名称推测）可能支持对上传的文件进行自动翻译。

## 技术栈

* **后端:**
    * Python 3.x
    * Flask (Web 框架)
    * (其他依赖请参见 `backend-python/requirements.txt`)
* **前端:**
    * Vue.js (JavaScript 框架)
    * Vue Router (路由管理)
    * Vuex (状态管理)
    * Node.js / npm (或 yarn)

## 项目结构
```plaintext
auto-translate/
├── backend-python/        # 后端 Flask 应用
│   ├── app.py             # 应用入口
│   ├── config.py          # 配置文件 (可能需要创建或修改)
│   ├── models.py          # 数据模型 (如果使用数据库)
│   ├── requirements.txt   # Python 依赖
│   ├── routes/            # API 路由蓝图
│   │   ├── __init__.py
│   │   ├── files.py       # 文件相关 API
│   │   └── projects.py    # 项目相关 API
│   ├── utils.py           # 工具函数
│   ├── data/              # (可能) 用于存储上传的文件和数据
│   └── ...
├── frontend-vue/          # 前端 Vue.js 应用
│   ├── public/
│   │   └── index.html     # HTML 入口文件
│   ├── src/
│   │   ├── assets/        # 静态资源
│   │   ├── components/    # Vue 组件
│   │   ├── router/        # 路由配置
│   │   ├── store/         # Vuex 状态管理
│   │   ├── views/         # 页面视图
│   │   └── main.js        # Vue 应用入口
│   ├── babel.config.js    # Babel 配置
│   ├── jsconfig.json      # JS 配置
│   ├── package.json       # npm 依赖和脚本
│   ├── vue.config.js      # Vue CLI 配置
│   └── ...
```

## 安装与运行

### 后端 (Flask)

1.  **环境准备:**
    * 确保已安装 Python 3.x 和 pip。
2.  **克隆仓库 (如果适用):**
    ```bash
    git clone <your-repository-url>
    cd auto-translate/backend-python
    ```
3.  **创建并激活虚拟环境 (推荐):**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
4.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **配置 (如果需要):**
    * 检查 `config.py` 文件。可能需要设置数据库连接、密钥或其他配置。根据需要创建或修改此文件。
6.  **运行开发服务器:**
    ```bash
    # 通常是以下命令之一，具体取决于 app.py 的设置
    python app.py
    # 或者
    flask run
    ```
    * 后端服务默认可能运行在 `http://127.0.0.1:5000` 或类似的地址。

### 前端 (Vue.js)

1.  **环境准备:**
    * 确保已安装 Node.js (自带 npm) 或 yarn。
2.  **导航到前端目录:**
    ```bash
    cd ../frontend-vue
    # 或者从项目根目录
    # cd auto-translate/frontend-vue
    ```
3.  **安装依赖:**
    ```bash
    # 使用 npm
    npm install

    # 或者使用 yarn
    yarn install
    ```
4.  **配置 (如果需要):**
    * 检查 `vue.config.js` 或 `src/` 目录下的配置文件。可能需要配置后端 API 的地址（例如，指向 `http://127.0.0.1:5000/api`）。
5.  **运行开发服务器:**
    ```bash
    # 使用 npm
    npm run serve

    # 或者使用 yarn
    yarn serve
    ```
    * 前端开发服务器通常运行在 `http://localhost:8080` 或类似的地址。在浏览器中打开此地址即可访问应用。
6.  **构建生产版本:**
    ```bash
    # 使用 npm
    npm run build

    # 或者使用 yarn
    yarn build
    ```
    * 构建后的文件会出现在 `dist/` 目录下。

## 使用方法

1.  确保后端服务正在运行。
2.  确保前端开发服务器正在运行。
3.  在浏览器中打开前端应用的地址 (例如 `http://localhost:8080`)。
4.  通过界面进行项目和文件的管理操作。

## API 端点 (示例)

后端提供以下 API 端点（具体请参见 `routes/` 下的文件）：

* **项目:**
    * `GET /api/projects`: 获取所有项目列表。
    * `POST /api/projects`: 创建新项目。
    * `GET /api/projects/<project_id>`: 获取单个项目详情。
    * `PUT /api/projects/<project_id>`: 更新项目信息。
    * `DELETE /api/projects/<project_id>`: 删除项目。
* **文件:**
    * `POST /api/projects/<project_id>/files`: 在指定项目中上传文件。
    * `GET /api/files/<file_id>`: 获取文件信息或内容。
    * `DELETE /api/files/<file_id>`: 删除文件。
    * `POST /api/files/<file_id>/translate`: （可能）触发文件翻译。

*(注意: 上述 API 路径可能需要根据 `app.py` 和蓝图注册的具体情况进行调整，例如可能包含 `/api` 前缀)*

## 贡献

(如果希望他人贡献，请在此处添加贡献指南。)

## 许可证

(如果项目有许可证，请在此处说明，例如 MIT, Apache 2.0 等。)
