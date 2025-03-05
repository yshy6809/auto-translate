const express = require('express');
const cors = require('cors');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

// 创建Express应用
const app = express();
const port = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json());

// 确保数据存储目录存在
const DATA_DIR = path.join(__dirname, 'data');
const PROJECTS_DIR = path.join(DATA_DIR, 'projects');
const DB_FILE = path.join(DATA_DIR, 'database.json');

// 创建必要的目录
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR);
}

if (!fs.existsSync(PROJECTS_DIR)) {
    fs.mkdirSync(PROJECTS_DIR);
}

// 初始化数据库文件
if (!fs.existsSync(DB_FILE)) {
    fs.writeFileSync(DB_FILE, JSON.stringify({ 
        projects: [],
        files: [] // 保留原有结构以便兼容
    }));
} else {
    // 如果数据库已存在但没有projects字段，添加它
    const db = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
    if (!db.projects) {
        db.projects = [];
        fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
    }
}

// 配置文件上传
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const projectId = req.params.projectId;
        
        // 创建项目文件目录（如果不存在）
        const projectDir = path.join(PROJECTS_DIR, projectId);
        const projectFilesDir = path.join(projectDir, 'files');
        
        if (!fs.existsSync(projectDir)) {
            fs.mkdirSync(projectDir);
        }
        
        if (!fs.existsSync(projectFilesDir)) {
            fs.mkdirSync(projectFilesDir);
        }
        
        cb(null, projectFilesDir);
    },
    filename: function (req, file, cb) {
        const fileId = uuidv4();
        const fileExtension = path.extname(file.originalname);
        cb(null, `${fileId}${fileExtension}`);
    }
});

const upload = multer({ storage: storage });

// 数据库操作
function readDatabase() {
    const data = fs.readFileSync(DB_FILE, 'utf8');
    return JSON.parse(data);
}

function writeDatabase(data) {
    fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
}

// 解析文件内容
function parseFileContent(content) {
    // 假设文件格式是每段用空行分隔
    // 在实际应用中，根据具体文件格式修改此解析逻辑
    return content.split(/\n\s*\n/).filter(segment => segment.trim() !== '');
}

// 计算项目完成率
function updateProjectCompletionRate(db, projectIndex) {
    const project = db.projects[projectIndex];
    
    if (project.files.length === 0) {
        project.completionRate = 0;
        return;
    }
    
    let totalSegments = 0;
    let completedSegments = 0;
    
    // 计算所有文件的总段落数和已完成段落数
    project.files.forEach(file => {
        totalSegments += file.originalSegments.length;
        completedSegments += file.translatedSegments.filter(s => s.trim() !== '').length;
    });
    
    // 计算完成率（百分比）
    project.completionRate = totalSegments > 0 ? Math.round((completedSegments / totalSegments) * 100) : 0;
}

// API 路由

// =========================
// 项目相关 API
// =========================

// 获取所有项目
app.get('/api/projects', (req, res) => {
    try {
        const db = readDatabase();
        res.json(db.projects);
    } catch (error) {
        console.error('获取项目列表出错:', error);
        res.status(500).json({ error: '获取项目列表失败' });
    }
});

// 创建新项目
app.post('/api/projects', (req, res) => {
    try {
        const { name, description } = req.body;
        
        if (!name) {
            return res.status(400).json({ error: '缺少项目名称' });
        }
        
        const projectId = uuidv4();
        const now = new Date().toISOString();
        
        // 创建项目目录
        const projectDir = path.join(PROJECTS_DIR, projectId);
        const projectFilesDir = path.join(projectDir, 'files');
        
        if (!fs.existsSync(projectDir)) {
            fs.mkdirSync(projectDir);
        }
        
        if (!fs.existsSync(projectFilesDir)) {
            fs.mkdirSync(projectFilesDir);
        }
        
        // 将项目信息添加到数据库
        const db = readDatabase();
        const newProject = {
            id: projectId,
            name,
            description: description || '',
            creationDate: now,
            lastModified: now,
            files: [],
            completionRate: 0
        };
        
        db.projects.push(newProject);
        writeDatabase(db);
        
        res.status(201).json({ 
            id: projectId, 
            message: '项目创建成功',
            project: newProject
        });
    } catch (error) {
        console.error('创建项目出错:', error);
        res.status(500).json({ error: '创建项目失败' });
    }
});

// 获取特定项目详情
app.get('/api/projects/:id', (req, res) => {
    try {
        const projectId = req.params.id;
        const db = readDatabase();
        const project = db.projects.find(p => p.id === projectId);
        
        if (!project) {
            return res.status(404).json({ error: '项目不存在' });
        }
        
        res.json(project);
    } catch (error) {
        console.error('获取项目详情出错:', error);
        res.status(500).json({ error: '获取项目详情失败' });
    }
});

// 更新项目信息
app.put('/api/projects/:id', (req, res) => {
    try {
        const projectId = req.params.id;
        const { name, description } = req.body;
        
        const db = readDatabase();
        const projectIndex = db.projects.findIndex(p => p.id === projectId);
        
        if (projectIndex === -1) {
            return res.status(404).json({ error: '项目不存在' });
        }
        
        // 更新项目信息
        if (name) {
            db.projects[projectIndex].name = name;
        }
        
        if (description !== undefined) {
            db.projects[projectIndex].description = description;
        }
        
        db.projects[projectIndex].lastModified = new Date().toISOString();
        
        writeDatabase(db);
        
        res.json({ 
            message: '项目信息已更新',
            project: db.projects[projectIndex]
        });
    } catch (error) {
        console.error('更新项目信息出错:', error);
        res.status(500).json({ error: '更新项目信息失败' });
    }
});

// 删除项目
app.delete('/api/projects/:id', (req, res) => {
    try {
        const projectId = req.params.id;
        const db = readDatabase();
        const projectIndex = db.projects.findIndex(p => p.id === projectId);
        
        if (projectIndex === -1) {
            return res.status(404).json({ error: '项目不存在' });
        }
        
        const projectDir = path.join(PROJECTS_DIR, projectId);
        
        // 删除项目目录及文件
        if (fs.existsSync(projectDir)) {
            // 递归删除目录
            fs.rmSync(projectDir, { recursive: true, force: true });
        }
        
        // 从数据库中删除
        db.projects.splice(projectIndex, 1);
        writeDatabase(db);
        
        res.json({ message: '项目已删除' });
    } catch (error) {
        console.error('删除项目出错:', error);
        res.status(500).json({ error: '删除项目失败' });
    }
});

// =========================
// 项目文件相关 API
// =========================

// 获取项目中的所有文件
app.get('/api/projects/:projectId/files', (req, res) => {
    try {
        const projectId = req.params.projectId;
        const db = readDatabase();
        const project = db.projects.find(p => p.id === projectId);
        
        if (!project) {
            return res.status(404).json({ error: '项目不存在' });
        }
        
        res.json(project.files);
    } catch (error) {
        console.error('获取项目文件列表出错:', error);
        res.status(500).json({ error: '获取项目文件列表失败' });
    }
});

// 上传文件到项目
app.post('/api/projects/:projectId/files', upload.single('file'), (req, res) => {
    try {
        const projectId = req.params.projectId;
        
        if (!req.file) {
            return res.status(400).json({ error: '没有上传文件' });
        }
        
        const db = readDatabase();
        const projectIndex = db.projects.findIndex(p => p.id === projectId);
        
        if (projectIndex === -1) {
            return res.status(404).json({ error: '项目不存在' });
        }
        
        const fileId = path.basename(req.file.filename, path.extname(req.file.filename));
        const originalFileName = req.file.originalname;
        const filePath = req.file.path;
        
        // 读取文件内容
        const fileContent = fs.readFileSync(filePath, 'utf8');
        const originalSegments = parseFileContent(fileContent);
        const translatedSegments = new Array(originalSegments.length).fill('');
        
        // 将文件信息添加到项目
        const newFile = {
            id: fileId,
            fileName: originalFileName,
            filePath: filePath,
            uploadDate: new Date().toISOString(),
            originalSegments: originalSegments,
            translatedSegments: translatedSegments,
            completionRate: 0
        };
        
        db.projects[projectIndex].files.push(newFile);
        db.projects[projectIndex].lastModified = new Date().toISOString();
        
        // 更新项目完成率
        updateProjectCompletionRate(db, projectIndex);
        
        writeDatabase(db);
        
        res.status(201).json({ 
            id: fileId, 
            message: '文件上传成功',
            file: newFile
        });
    } catch (error) {
        console.error('上传项目文件出错:', error);
        res.status(500).json({ error: '上传项目文件失败' });
    }
});

// 获取项目中的特定文件
app.get('/api/projects/:projectId/files/:fileId', (req, res) => {
    try {
        const { projectId, fileId } = req.params;
        const db = readDatabase();
        const project = db.projects.find(p => p.id === projectId);
        
        if (!project) {
            return res.status(404).json({ error: '项目不存在' });
        }
        
        const file = project.files.find(f => f.id === fileId);
        
        if (!file) {
            return res.status(404).json({ error: '文件不存在' });
        }
        
        res.json(file);
    } catch (error) {
        console.error('获取项目文件内容出错:', error);
        res.status(500).json({ error: '获取项目文件内容失败' });
    }
});

// 更新项目文件翻译内容
app.put('/api/projects/:projectId/files/:fileId', (req, res) => {
    try {
        const { projectId, fileId } = req.params;
        const translatedSegments = req.body.translatedSegments;
        
        if (!translatedSegments) {
            return res.status(400).json({ error: '缺少翻译内容' });
        }
        
        const db = readDatabase();
        const projectIndex = db.projects.findIndex(p => p.id === projectId);
        
        if (projectIndex === -1) {
            return res.status(404).json({ error: '项目不存在' });
        }
        
        const fileIndex = db.projects[projectIndex].files.findIndex(f => f.id === fileId);
        
        if (fileIndex === -1) {
            return res.status(404).json({ error: '文件不存在' });
        }
        
        // 更新翻译内容
        db.projects[projectIndex].files[fileIndex].translatedSegments = translatedSegments;
        db.projects[projectIndex].lastModified = new Date().toISOString();
        
        // 计算文件完成率
        const totalSegments = db.projects[projectIndex].files[fileIndex].originalSegments.length;
        const completedSegments = translatedSegments.filter(s => s.trim() !== '').length;
        const completionRate = totalSegments > 0 ? Math.round((completedSegments / totalSegments) * 100) : 0;
        
        db.projects[projectIndex].files[fileIndex].completionRate = completionRate;
        
        // 更新项目完成率
        updateProjectCompletionRate(db, projectIndex);
        
        writeDatabase(db);
        
        res.json({ 
            message: '翻译内容已更新', 
            completionRate,
            projectCompletionRate: db.projects[projectIndex].completionRate 
        });
    } catch (error) {
        console.error('更新项目文件翻译内容出错:', error);
        res.status(500).json({ error: '更新项目文件翻译内容失败' });
    }
});

// 删除项目文件
app.delete('/api/projects/:projectId/files/:fileId', (req, res) => {
    try {
        const { projectId, fileId } = req.params;
        const db = readDatabase();
        const projectIndex = db.projects.findIndex(p => p.id === projectId);
        
        if (projectIndex === -1) {
            return res.status(404).json({ error: '项目不存在' });
        }
        
        const fileIndex = db.projects[projectIndex].files.findIndex(f => f.id === fileId);
        
        if (fileIndex === -1) {
            return res.status(404).json({ error: '文件不存在' });
        }
        
        const filePath = db.projects[projectIndex].files[fileIndex].filePath;
        
        // 删除物理文件
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
        
        // 从项目中删除文件
        db.projects[projectIndex].files.splice(fileIndex, 1);
        db.projects[projectIndex].lastModified = new Date().toISOString();
        
        // 更新项目完成率
        updateProjectCompletionRate(db, projectIndex);
        
        writeDatabase(db);
        
        res.json({ message: '文件已从项目中删除' });
    } catch (error) {
        console.error('删除项目文件出错:', error);
        res.status(500).json({ error: '删除项目文件失败' });
    }
});

// 下载项目文件翻译内容
app.get('/api/projects/:projectId/files/:fileId/download', (req, res) => {
    try {
        const { projectId, fileId } = req.params;
        const db = readDatabase();
        const project = db.projects.find(p => p.id === projectId);
        
        if (!project) {
            return res.status(404).json({ error: '项目不存在' });
        }
        
        const file = project.files.find(f => f.id === fileId);
        
        if (!file) {
            return res.status(404).json({ error: '文件不存在' });
        }
        
        // 检查是否所有段落都已翻译
        const allTranslated = file.translatedSegments.every(s => s.trim() !== '');
        if (!allTranslated) {
            return res.status(400).json({ error: '翻译尚未完成' });
        }
        
        // 生成翻译后的文件内容
        const translatedContent = file.translatedSegments.join('\n\n');
        
        // 设置响应头
        const downloadFileName = file.fileName.replace('.txt', '-translated.txt');
        res.setHeader('Content-Disposition', `attachment; filename="${downloadFileName}"`);
        res.setHeader('Content-Type', 'text/plain');
        
        // 发送文件内容
        res.send(translatedContent);
    } catch (error) {
        console.error('下载项目文件翻译出错:', error);
        res.status(500).json({ error: '下载项目文件翻译失败' });
    }
});

// =========================
// 兼容旧的API路由（向下兼容）
// =========================

// 获取所有文件列表（合并所有项目中的文件）
app.get('/api/files', (req, res) => {
    try {
        const db = readDatabase();
        // 返回所有项目中的文件和原始files数组中的文件
        const allFiles = [
            ...db.files,
            ...db.projects.flatMap(project => project.files.map(file => ({
                ...file,
                projectId: project.id, // 添加项目ID以便识别
                projectName: project.name
            })))
        ];
        res.json(allFiles);
    } catch (error) {
        console.error('获取文件列表出错:', error);
        res.status(500).json({ error: '获取文件列表失败' });
    }
});

// 上传新文件（创建默认项目并上传到该项目）
app.post('/api/files', upload.single('file'), (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: '没有上传文件' });
        }

        const db = readDatabase();
        
        // 确保有默认项目
        let defaultProject = db.projects.find(p => p.name === '默认项目');
        let defaultProjectIndex = db.projects.findIndex(p => p.name === '默认项目');
        
        if (!defaultProject) {
            const defaultProjectId = uuidv4();
            defaultProject = {
                id: defaultProjectId,
                name: '默认项目',
                description: '自动创建的默认项目，存储未分类文件',
                creationDate: new Date().toISOString(),
                lastModified: new Date().toISOString(),
                files: [],
                completionRate: 0
            };
            
            db.projects.push(defaultProject);
            defaultProjectIndex = db.projects.length - 1;
            
            // 创建默认项目目录
            const projectDir = path.join(PROJECTS_DIR, defaultProjectId);
            const projectFilesDir = path.join(projectDir, 'files');
            
            if (!fs.existsSync(projectDir)) {
                fs.mkdirSync(projectDir);
            }
            
            if (!fs.existsSync(projectFilesDir)) {
                fs.mkdirSync(projectFilesDir);
            }
            
            // 移动上传的文件到默认项目目录
            const tempFilePath = req.file.path;
            const targetFilePath = path.join(projectFilesDir, req.file.filename);
            
            if (tempFilePath !== targetFilePath) {
                fs.renameSync(tempFilePath, targetFilePath);
            }
        }
        
        const fileId = path.basename(req.file.filename, path.extname(req.file.filename));
        const originalFileName = req.file.originalname;
        const filePath = path.join(PROJECTS_DIR, defaultProject.id, 'files', req.file.filename);

        // 读取文件内容
        const fileContent = fs.readFileSync(req.file.path, 'utf8');
        const originalSegments = parseFileContent(fileContent);
        const translatedSegments = new Array(originalSegments.length).fill('');

        // 将文件信息添加到默认项目
        const newFile = {
            id: fileId,
            fileName: originalFileName,
            filePath: filePath,
            uploadDate: new Date().toISOString(),
            originalSegments: originalSegments,
            translatedSegments: translatedSegments,
            completionRate: 0
        };

        db.projects[defaultProjectIndex].files.push(newFile);
        db.projects[defaultProjectIndex].lastModified = new Date().toISOString();
        
        // 同时添加到旧的文件数组以保持兼容性
        db.files.push({
            ...newFile,
            projectId: defaultProject.id,
            projectName: defaultProject.name
        });
        
        writeDatabase(db);

        res.status(201).json({ 
            id: fileId, 
            projectId: defaultProject.id,
            message: '文件上传成功' 
        });
    } catch (error) {
        console.error('上传文件出错:', error);
        res.status(500).json({ error: '上传文件失败' });
    }
});

// 获取特定文件内容
app.get('/api/files/:id', (req, res) => {
    try {
        const fileId = req.params.id;
        const db = readDatabase();
        
        // 先在旧文件数组中查找
        let file = db.files.find(f => f.id === fileId);
        
        // 如果没找到，在所有项目中查找
        if (!file) {
            for (const project of db.projects) {
                const projectFile = project.files.find(f => f.id === fileId);
                if (projectFile) {
                    file = {
                        ...projectFile,
                        projectId: project.id,
                        projectName: project.name
                    };
                    break;
                }
            }
        }

        if (!file) {
            return res.status(404).json({ error: '文件不存在' });
        }

        res.json(file);
    } catch (error) {
        console.error('获取文件内容出错:', error);
        res.status(500).json({ error: '获取文件内容失败' });
    }
});

// 更新文件翻译内容
app.put('/api/files/:id', (req, res) => {
    try {
        const fileId = req.params.id;
        const translatedSegments = req.body.translatedSegments;

        if (!translatedSegments) {
            return res.status(400).json({ error: '缺少翻译内容' });
        }

        const db = readDatabase();
        const fileIndex = db.files.findIndex(f => f.id === fileId);
        let file, projectIndex, projectFileIndex, projectId;
        
        // 先检查旧文件数组
        if (fileIndex !== -1) {
            // 找到文件在旧数组中，更新
            db.files[fileIndex].translatedSegments = translatedSegments;
            
            // 计算完成率
            const totalSegments = db.files[fileIndex].originalSegments.length;
            const completedSegments = translatedSegments.filter(s => s.trim() !== '').length;
            const completionRate = totalSegments > 0 ? Math.round((completedSegments / totalSegments) * 100) : 0;
            
            db.files[fileIndex].completionRate = completionRate;
            
            // 如果文件有项目信息，同时更新项目中的文件
            if (db.files[fileIndex].projectId) {
                projectId = db.files[fileIndex].projectId;
                projectIndex = db.projects.findIndex(p => p.id === projectId);
                
                if (projectIndex !== -1) {
                    projectFileIndex = db.projects[projectIndex].files.findIndex(f => f.id === fileId);
                    
                    if (projectFileIndex !== -1) {
                        db.projects[projectIndex].files[projectFileIndex].translatedSegments = translatedSegments;
                        db.projects[projectIndex].files[projectFileIndex].completionRate = completionRate;
                        db.projects[projectIndex].lastModified = new Date().toISOString();
                        
                        // 更新项目完成率
                        updateProjectCompletionRate(db, projectIndex);
                    }
                }
            }
            
            writeDatabase(db);
            
            return res.json({ message: '翻译内容已更新', completionRate });
        }
        
        // 在所有项目中查找
        let found = false;
        for (let i = 0; i < db.projects.length; i++) {
            const fileIdx = db.projects[i].files.findIndex(f => f.id === fileId);
            if (fileIdx !== -1) {
                // 更新翻译内容
                db.projects[i].files[fileIdx].translatedSegments = translatedSegments;
                
                // 计算完成率
                const totalSegments = db.projects[i].files[fileIdx].originalSegments.length;
                const completedSegments = translatedSegments.filter(s => s.trim() !== '').length;
                const completionRate = totalSegments > 0 ? Math.round((completedSegments / totalSegments) * 100) : 0;
                
                db.projects[i].files[fileIdx].completionRate = completionRate;
                db.projects[i].lastModified = new Date().toISOString();
                
                // 更新项目完成率
                updateProjectCompletionRate(db, i);
                
                writeDatabase(db);
                
                found = true;
                return res.json({ 
                    message: '翻译内容已更新', 
                    completionRate,
                    projectCompletionRate: db.projects[i].completionRate
                });
            }
        }

        if (!found) {
            return res.status(404).json({ error: '文件不存在' });
        }
    } catch (error) {
        console.error('更新翻译内容出错:', error);
        res.status(500).json({ error: '更新翻译内容失败' });
    }
});

// 删除文件
app.delete('/api/files/:id', (req, res) => {
    try {
        const fileId = req.params.id;
        const db = readDatabase();
        const fileIndex = db.files.findIndex(f => f.id === fileId);

        // 先尝试从旧文件数组中删除
        if (fileIndex !== -1) {
            const filePath = db.files[fileIndex].filePath;
            const projectId = db.files[fileIndex].projectId;
            
            // 如果有项目ID，也从项目中删除
            if (projectId) {
                const projectIndex = db.projects.findIndex(p => p.id === projectId);
                if (projectIndex !== -1) {
                    const projectFileIndex = db.projects[projectIndex].files.findIndex(f => f.id === fileId);
                    if (projectFileIndex !== -1) {
                        db.projects[projectIndex].files.splice(projectFileIndex, 1);
                        db.projects[projectIndex].lastModified = new Date().toISOString();
                        
                        // 更新项目完成率
                        updateProjectCompletionRate(db, projectIndex);
                    }
                }
            }
            
            // 删除物理文件
            if (fs.existsSync(filePath)) {
                fs.unlinkSync(filePath);
            }
            
            // 从数据库中删除
            db.files.splice(fileIndex, 1);
            writeDatabase(db);
            
            return res.json({ message: '文件已删除' });
        }
        
        // 如果不在旧数组中，在所有项目中查找
        let found = false;
        for (let i = 0; i < db.projects.length; i++) {
            const fileIdx = db.projects[i].files.findIndex(f => f.id === fileId);
            if (fileIdx !== -1) {
                const filePath = db.projects[i].files[fileIdx].filePath;
                
                // 删除物理文件
                if (fs.existsSync(filePath)) {
                    fs.unlinkSync(filePath);
                }
                
                // 从项目中删除
                db.projects[i].files.splice(fileIdx, 1);
                db.projects[i].lastModified = new Date().toISOString();
                
                // 更新项目完成率
                updateProjectCompletionRate(db, i);
                
                writeDatabase(db);
                found = true;
                return res.json({ message: '文件已删除' });
            }
        }

        if (!found) {
            return res.status(404).json({ error: '文件不存在' });
        }
    } catch (error) {
        console.error('删除文件出错:', error);
        res.status(500).json({ error: '删除文件失败' });
    }
});

// 下载翻译后的文件
app.get('/api/files/:id/download', (req, res) => {
    try {
        const fileId = req.params.id;
        const db = readDatabase();
        
        // 先在旧文件数组中查找
        let file = db.files.find(f => f.id === fileId);
        
        // 如果没找到，在所有项目中查找
        if (!file) {
            for (const project of db.projects) {
                const projectFile = project.files.find(f => f.id === fileId);
                if (projectFile) {
                    file = projectFile;
                    break;
                }
            }
        }

        if (!file) {
            return res.status(404).json({ error: '文件不存在' });
        }

        // 检查是否所有段落都已翻译
        const allTranslated = file.translatedSegments.every(s => s.trim() !== '');
        if (!allTranslated) {
            return res.status(400).json({ error: '翻译尚未完成' });
        }

        // 生成翻译后的文件内容
        const translatedContent = file.translatedSegments.join('\n\n');
        
        // 设置响应头
        const downloadFileName = file.fileName.replace('.txt', '-translated.txt');
        res.setHeader('Content-Disposition', `attachment; filename="${downloadFileName}"`);
        res.setHeader('Content-Type', 'text/plain');
        
        // 发送文件内容
        res.send(translatedContent);
    } catch (error) {
        console.error('下载翻译文件出错:', error);
        res.status(500).json({ error: '下载翻译文件失败' });
    }
});

// 启动服务器
app.listen(port, () => {
    console.log(`翻译服务器运行在 http://localhost:${port}`);
});