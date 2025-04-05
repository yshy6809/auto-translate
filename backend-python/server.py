import os
import json
import shutil
import uuid
import re
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models import db, Project, File, LegacyFile

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大16MB上传

# 配置SQLite数据库
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PROJECTS_DIR = os.path.join(DATA_DIR, 'projects')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(DATA_DIR, "database.sqlite")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化SQLAlchemy
db.init_app(app)

# 确保数据库和表存在
with app.app_context():
    db.create_all()

# 解析文件内容
def parse_file_content(content):
    """将文本内容分割为段落"""
    return [segment for segment in re.split(r'\n\s*\n', content) if segment.strip()]

# API 路由

# =========================
# 项目相关 API
# =========================

# 获取所有项目
@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        projects = Project.query.all()
        return jsonify([project.to_dict() for project in projects])
    except Exception as e:
        app.logger.error(f'获取项目列表出错: {str(e)}')
        return jsonify({'error': '获取项目列表失败'}), 500

# 创建新项目
@app.route('/api/projects', methods=['POST'])
def create_project():
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return jsonify({'error': '缺少项目名称'}), 400
        
        project_id = str(uuid.uuid4())
        now = datetime.now()
        
        # 创建项目目录
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        project_files_dir = os.path.join(project_dir, 'files')
        
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(project_files_dir, exist_ok=True)
        
        # 创建新项目
        new_project = Project(
            id=project_id,
            name=name,
            description=description,
            creation_date=now,
            last_modified=now,
            completion_rate=0
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        project_dict = new_project.to_dict()
        
        return jsonify({
            'id': project_id,
            'message': '项目创建成功',
            'project': project_dict
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'创建项目出错: {str(e)}')
        return jsonify({'error': '创建项目失败'}), 500

# 获取特定项目详情
@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        return jsonify(project.to_dict())
    except Exception as e:
        app.logger.error(f'获取项目详情出错: {str(e)}')
        return jsonify({'error': '获取项目详情失败'}), 500

# 更新项目信息
@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description')
        
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        # 更新项目信息
        if name:
            project.name = name
        
        if description is not None:
            project.description = description
        
        project.last_modified = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'message': '项目信息已更新',
            'project': project.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'更新项目信息出错: {str(e)}')
        return jsonify({'error': '更新项目信息失败'}), 500

# 删除项目
@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        
        # 删除项目目录及文件
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        
        # 从数据库中删除
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'message': '项目已删除'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'删除项目出错: {str(e)}')
        return jsonify({'error': '删除项目失败'}), 500

# =========================
# 项目文件相关 API
# =========================

# 获取项目中的所有文件
@app.route('/api/projects/<project_id>/files', methods=['GET'])
def get_project_files(project_id):
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        files = File.query.filter_by(project_id=project_id).all()
        return jsonify([file.to_dict() for file in files])
    except Exception as e:
        app.logger.error(f'获取项目文件列表出错: {str(e)}')
        return jsonify({'error': '获取项目文件列表失败'}), 500

# 上传文件到项目
@app.route('/api/projects/<project_id>/files', methods=['POST'])
def upload_file_to_project(project_id):
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        # 确保项目文件目录存在
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        project_files_dir = os.path.join(project_dir, 'files')
        
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(project_files_dir, exist_ok=True)
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(project_files_dir, filename)
        
        # 保存文件
        file.save(file_path)
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        original_segments = parse_file_content(file_content)
        
        # 创建新文件记录
        new_file = File(
            id=file_id,
            file_name=original_filename,
            file_path=file_path,
            upload_date=datetime.now(),
            project_id=project_id,
            completion_rate=0
        )
        
        # 设置段落内容
        new_file.original_segments_list = original_segments
        new_file.translated_segments_list = [''] * len(original_segments)
        
        # 更新项目修改时间
        project.last_modified = datetime.now()
        
        db.session.add(new_file)
        db.session.commit()
        
        # 更新项目完成率
        project.update_completion_rate()
        db.session.commit()
        
        return jsonify({
            'id': file_id,
            'message': '文件上传成功',
            'file': new_file.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'上传项目文件出错: {str(e)}')
        return jsonify({'error': '上传项目文件失败'}), 500

# 获取项目中的特定文件
@app.route('/api/projects/<project_id>/files/<file_id>', methods=['GET'])
def get_project_file(project_id, file_id):
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        file = File.query.filter_by(id=file_id, project_id=project_id).first()
        
        if not file:
            return jsonify({'error': '文件不存在'}), 404
        
        return jsonify(file.to_dict())
    except Exception as e:
        app.logger.error(f'获取项目文件内容出错: {str(e)}')
        return jsonify({'error': '获取项目文件内容失败'}), 500

# 更新项目文件翻译内容
@app.route('/api/projects/<project_id>/files/<file_id>', methods=['PUT'])
def update_project_file_translation(project_id, file_id):
    try:
        data = request.json
        translated_segments = data.get('translatedSegments')
        
        if not translated_segments:
            return jsonify({'error': '缺少翻译内容'}), 400
        
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        file = File.query.filter_by(id=file_id, project_id=project_id).first()
        
        if not file:
            return jsonify({'error': '文件不存在'}), 404
        
        # 更新翻译内容
        file.translated_segments_list = translated_segments
        project.last_modified = datetime.now()
        
        # 更新文件完成率
        file.update_completion_rate()
        
        # 更新项目完成率
        project.update_completion_rate()
        
        db.session.commit()
        
        return jsonify({
            'message': '翻译内容已更新',
            'completionRate': file.completion_rate,
            'projectCompletionRate': project.completion_rate
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'更新项目文件翻译内容出错: {str(e)}')
        return jsonify({'error': '更新项目文件翻译内容失败'}), 500

# 删除项目文件
@app.route('/api/projects/<project_id>/files/<file_id>', methods=['DELETE'])
def delete_project_file(project_id, file_id):
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        file = File.query.filter_by(id=file_id, project_id=project_id).first()
        
        if not file:
            return jsonify({'error': '文件不存在'}), 404
        
        file_path = file.file_path
        
        # 删除物理文件
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 从数据库中删除文件
        db.session.delete(file)
        
        # 更新项目修改时间
        project.last_modified = datetime.now()
        
        db.session.commit()
        
        # 更新项目完成率
        project.update_completion_rate()
        db.session.commit()
        
        return jsonify({'message': '文件已从项目中删除'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'删除项目文件出错: {str(e)}')
        return jsonify({'error': '删除项目文件失败'}), 500

# 下载项目文件翻译内容
@app.route('/api/projects/<project_id>/files/<file_id>/download', methods=['GET'])
def download_project_file(project_id, file_id):
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        file = File.query.filter_by(id=file_id, project_id=project_id).first()
        
        if not file:
            return jsonify({'error': '文件不存在'}), 404
        
        # 检查是否所有段落都已翻译
        all_translated = all(s.strip() for s in file.translated_segments_list)
        if not all_translated:
            return jsonify({'error': '翻译尚未完成'}), 400
        
        # 生成翻译后的文件内容
        translated_content = '\n\n'.join(file.translated_segments_list)
        
        # 创建临时文件
        download_filename = file.file_name.replace('.txt', '-translated.txt')
        temp_path = os.path.join(DATA_DIR, download_filename)
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='text/plain'
        )
    except Exception as e:
        app.logger.error(f'下载项目文件翻译出错: {str(e)}')
        return jsonify({'error': '下载项目文件翻译失败'}), 500

# =========================
# 兼容旧的API路由（向下兼容）
# =========================

# 获取所有文件列表（合并所有项目中的文件）
@app.route('/api/files', methods=['GET'])
def get_files():
    try:
        # 获取旧文件
        legacy_files = LegacyFile.query.all()
        legacy_file_dicts = [file.to_dict() for file in legacy_files]
        
        # 获取所有项目文件
        project_files = []
        projects = Project.query.all()
        
        for project in projects:
            files = File.query.filter_by(project_id=project.id).all()
            for file in files:
                file_dict = file.to_dict()
                file_dict['projectId'] = project.id
                file_dict['projectName'] = project.name
                project_files.append(file_dict)
        
        # 合并结果
        all_files = legacy_file_dicts + project_files
        
        return jsonify(all_files)
    except Exception as e:
        app.logger.error(f'获取文件列表出错: {str(e)}')
        return jsonify({'error': '获取文件列表失败'}), 500

# 上传新文件（创建默认项目并上传到该项目）
@app.route('/api/files', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 确保有默认项目
        default_project = Project.query.filter_by(name='默认项目').first()
        
        if not default_project:
            default_project_id = str(uuid.uuid4())
            now = datetime.now()
            
            default_project = Project(
                id=default_project_id,
                name='默认项目',
                description='自动创建的默认项目，存储未分类文件',
                creation_date=now,
                last_modified=now,
                completion_rate=0
            )
            
            db.session.add(default_project)
            db.session.commit()
            
            # 创建默认项目目录
            project_dir = os.path.join(PROJECTS_DIR, default_project_id)
            project_files_dir = os.path.join(project_dir, 'files')
            
            os.makedirs(project_dir, exist_ok=True)
            os.makedirs(project_files_dir, exist_ok=True)
        else:
            project_files_dir = os.path.join(PROJECTS_DIR, default_project.id, 'files')
            os.makedirs(project_files_dir, exist_ok=True)
            
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(project_files_dir, filename)
        
        # 保存文件
        file.save(file_path)
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        original_segments = parse_file_content(file_content)
        
        # 创建项目文件记录
        new_file = File(
            id=file_id,
            file_name=original_filename,
            file_path=file_path,
            upload_date=datetime.now(),
            project_id=default_project.id,
            completion_rate=0
        )
        
        # 设置段落内容
        new_file.original_segments_list = original_segments
        new_file.translated_segments_list = [''] * len(original_segments)
        
        # 更新项目修改时间
        default_project.last_modified = datetime.now()
        
        db.session.add(new_file)
        
        # 同时添加到旧的文件表以保持兼容性
        legacy_file = LegacyFile(
            id=file_id,
            file_name=original_filename,
            file_path=file_path,
            upload_date=datetime.now(),
            completion_rate=0,
            project_id=default_project.id,
            project_name=default_project.name
        )
        
        # 设置段落内容
        legacy_file.original_segments_list = original_segments
        legacy_file.translated_segments_list = [''] * len(original_segments)
        
        db.session.add(legacy_file)
        db.session.commit()
        
        # 更新项目完成率
        default_project.update_completion_rate()
        db.session.commit()
        
        return jsonify({
            'id': file_id,
            'projectId': default_project.id,
            'message': '文件上传成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'上传文件出错: {str(e)}')
        return jsonify({'error': '上传文件失败'}), 500

# 获取特定文件内容
@app.route('/api/files/<file_id>', methods=['GET'])
def get_file(file_id):
    try:
        # 先在旧文件表中查找
        legacy_file = LegacyFile.query.get(file_id)
        
        if legacy_file:
            return jsonify(legacy_file.to_dict())
        
        # 如果没找到，在项目文件中查找
        file = File.query.get(file_id)
        
        if file:
            project = Project.query.get(file.project_id)
            file_dict = file.to_dict()
            file_dict['projectId'] = project.id
            file_dict['projectName'] = project.name
            return jsonify(file_dict)
        
        return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        app.logger.error(f'获取文件内容出错: {str(e)}')
        return jsonify({'error': '获取文件内容失败'}), 500

# 更新文件翻译内容
@app.route('/api/files/<file_id>', methods=['PUT'])
def update_file_translation(file_id):
    try:
        data = request.json
        translated_segments = data.get('translatedSegments')
        
        if not translated_segments:
            return jsonify({'error': '缺少翻译内容'}), 400
        
        # 先检查旧文件表
        legacy_file = LegacyFile.query.get(file_id)
        
        if legacy_file:
            # 更新旧文件翻译内容
            legacy_file.translated_segments_list = translated_segments
            
            # 更新完成率
            legacy_file.update_completion_rate()
            
            # 如果关联了项目，也更新项目文件
            if legacy_file.project_id:
                file = File.query.filter_by(id=file_id, project_id=legacy_file.project_id).first()
                if file:
                    file.translated_segments_list = translated_segments
                    file.update_completion_rate()
                    
                    # 更新项目
                    project = Project.query.get(file.project_id)
                    if project:
                        project.last_modified = datetime.now()
                        project.update_completion_rate()
            
            db.session.commit()
            
            return jsonify({
                'message': '翻译内容已更新',
                'completionRate': legacy_file.completion_rate
            })
            
        # 在项目文件中查找
        file = File.query.get(file_id)
        
        if file:
            # 更新文件翻译内容
            file.translated_segments_list = translated_segments
            file.update_completion_rate()
            
            # 更新项目
            project = Project.query.get(file.project_id)
            project.last_modified = datetime.now()
            project.update_completion_rate()
            
            db.session.commit()
            
            return jsonify({
                'message': '翻译内容已更新',
                'completionRate': file.completion_rate,
                'projectCompletionRate': project.completion_rate
            })
        
        return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'更新翻译内容出错: {str(e)}')
        return jsonify({'error': '更新翻译内容失败'}), 500

# 删除文件
@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    try:
        # 先检查旧文件表
        legacy_file = LegacyFile.query.get(file_id)
        
        if legacy_file:
            file_path = legacy_file.file_path
            project_id = legacy_file.project_id
            
            # 如果关联了项目，也删除项目文件
            if project_id:
                file = File.query.filter_by(id=file_id, project_id=project_id).first()
                if file:
                    db.session.delete(file)
                    
                    # 更新项目
                    project = Project.query.get(project_id)
                    if project:
                        project.last_modified = datetime.now()
                        db.session.commit()
                        project.update_completion_rate()
            
            # 删除物理文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 从数据库中删除
            db.session.delete(legacy_file)
            db.session.commit()
            
            return jsonify({'message': '文件已删除'})
            
        # 在项目文件中查找
        file = File.query.get(file_id)
        
        if file:
            file_path = file.file_path
            project_id = file.project_id
            
            # 删除物理文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 从数据库中删除
            db.session.delete(file)
            
            # 更新项目
            project = Project.query.get(project_id)
            project.last_modified = datetime.now()
            db.session.commit()
            
            project.update_completion_rate()
            db.session.commit()
            
            return jsonify({'message': '文件已删除'})
        
        return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'删除文件出错: {str(e)}')
        return jsonify({'error': '删除文件失败'}), 500

# 下载翻译后的文件
@app.route('/api/files/<file_id>/download', methods=['GET'])
def download_file(file_id):
    try:
        # 先在旧文件表中查找
        legacy_file = LegacyFile.query.get(file_id)
        
        if legacy_file:
            # 检查是否所有段落都已翻译
            all_translated = all(s.strip() for s in legacy_file.translated_segments_list)
            if not all_translated:
                return jsonify({'error': '翻译尚未完成'}), 400
            
            # 生成翻译后的文件内容
            translated_content = '\n\n'.join(legacy_file.translated_segments_list)
            
            # 创建临时文件
            download_filename = legacy_file.file_name.replace('.txt', '-translated.txt')
            temp_path = os.path.join(DATA_DIR, download_filename)
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=download_filename,
                mimetype='text/plain'
            )
            
        # 在项目文件中查找
        file = File.query.get(file_id)
        
        if file:
            # 检查是否所有段落都已翻译
            all_translated = all(s.strip() for s in file.translated_segments_list)
            if not all_translated:
                return jsonify({'error': '翻译尚未完成'}), 400
            
            # 生成翻译后的文件内容
            translated_content = '\n\n'.join(file.translated_segments_list)
            
            # 创建临时文件
            download_filename = file.file_name.replace('.txt', '-translated.txt')
            temp_path = os.path.join(DATA_DIR, download_filename)
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=download_filename,
                mimetype='text/plain'
            )
        
        return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        app.logger.error(f'下载翻译文件出错: {str(e)}')
        return jsonify({'error': '下载翻译文件失败'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)