import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
# 导入 Segment 模型
from models import db, Project, File, Segment
from utils import parse_file_content
from config import PROJECTS_DIR, DATA_DIR

# Create a Blueprint for project-specific file routes
# Note the dynamic part <project_id> in the url_prefix
files_bp = Blueprint('files', __name__, url_prefix='/api/projects/<project_id>/files')

# Get all files in a project
@files_bp.route('', methods=['GET'])
def get_project_files(project_id):
    try:
        # Ensure project exists first
        Project.query.get_or_404(project_id, description='项目不存在')

        files = File.query.filter_by(project_id=project_id).all()
        return jsonify([file.to_dict() for file in files])
    except Exception as e:
        current_app.logger.error(f'获取项目文件列表出错 (Project ID: {project_id}): {str(e)}')
        if hasattr(e, 'code') and e.code == 404:
             return jsonify({'error': '项目不存在'}), 404
        return jsonify({'error': '获取项目文件列表失败'}), 500

# Upload a file to a project
@files_bp.route('', methods=['POST'])
def upload_file_to_project(project_id):
    file_path = None # Initialize for potential cleanup
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400

        project = Project.query.get_or_404(project_id, description='项目不存在')

        # Ensure project file directory exists
        project_files_dir = os.path.join(PROJECTS_DIR, project_id, 'files')
        os.makedirs(project_files_dir, exist_ok=True) # Redundant if create_project worked, but safe

        # Generate unique filename
        file_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        # Ensure extension (handle cases like '.jpeg')
        _, file_extension = os.path.splitext(original_filename)
        if not file_extension:
             # Handle files without extensions if necessary, or default to .txt
             file_extension = '.txt' # Example default
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(project_files_dir, filename)

        # Save file
        file.save(file_path)

        # Read file content (handle potential encoding issues)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
             # Try other common encodings or return an error
             try:
                 with open(file_path, 'r', encoding='gbk') as f: # Example fallback
                     file_content = f.read()
             except Exception as read_err:
                 os.remove(file_path) # Clean up saved file if unreadable
                 current_app.logger.error(f'读取上传文件编码错误 (Path: {file_path}): {str(read_err)}')
                 return jsonify({'error': '无法读取文件内容，请确保文件为UTF-8编码'}), 400
        except Exception as read_err:
             os.remove(file_path) # Clean up saved file
             current_app.logger.error(f'读取上传文件时出错 (Path: {file_path}): {str(read_err)}')
             return jsonify({'error': '读取文件内容时出错'}), 500


        original_segments = parse_file_content(file_content)
        if not original_segments:
             os.remove(file_path) # Clean up empty file
             return jsonify({'error': '文件内容为空或无法解析为段落'}), 400

        # 解析后的原始段落列表
        original_segments_list = original_segments

        # 创建 File 记录 (不包含 segments)
        new_file = File(
            id=file_id,
            file_name=original_filename,
            file_path=file_path, # Store relative or absolute path based on need
            upload_date=datetime.now(),
            project_id=project_id,
            completion_rate=0 # 初始完成率为0
        )
        db.session.add(new_file)
        # 先提交 File 记录以获取 ID (如果需要) 或在添加 Segments 后一起提交
        # db.session.flush() # 可选：获取 new_file.id 但不结束事务

        # 创建 Segment 记录
        segments_to_add = []
        for index, text in enumerate(original_segments_list):
            segment = Segment(
                file_id=new_file.id, # 关联 File ID
                segment_index=index,
                original_text=text,
                translated_text='' # 初始翻译为空
            )
            segments_to_add.append(segment)

        if segments_to_add:
            db.session.add_all(segments_to_add)

        # 更新项目修改时间
        project.last_modified = datetime.now()

        # 提交所有更改 (File, Segments, Project time)
        db.session.commit()

        # 更新项目完成率 (现在 File 和 Segments 都已提交)
        # File 的完成率在创建时是0，可以在这里更新一次，或者依赖后续更新
        # new_file.update_completion_rate() # 更新单个文件完成率
        project.update_completion_rate()
        db.session.commit() # Commit project update

        return jsonify({
            'id': file_id,
            'message': '文件上传成功',
            'file': new_file.to_dict() # to_dict 会从 Segment 表获取数据
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'上传项目文件出错 (Project ID: {project_id}): {str(e)}')
        # Clean up saved file if it exists and DB operation failed
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as rm_error:
                current_app.logger.error(f'上传失败后清理文件时出错: {str(rm_error)}')
        if hasattr(e, 'code') and e.code == 404:
             return jsonify({'error': '项目不存在'}), 404
        return jsonify({'error': '上传项目文件失败'}), 500


# Get a specific file in a project
@files_bp.route('/<file_id>', methods=['GET'])
def get_project_file(project_id, file_id):
    try:
        # Ensure project exists first (optional, depends if file ID is globally unique)
        # Project.query.get_or_404(project_id, description='项目不存在')

        file = File.query.filter_by(id=file_id, project_id=project_id).first_or_404(
            description='文件不存在或不属于该项目'
        )
        return jsonify(file.to_dict())
    except Exception as e:
        current_app.logger.error(f'获取项目文件内容出错 (Project: {project_id}, File: {file_id}): {str(e)}')
        if hasattr(e, 'code') and e.code == 404:
             return jsonify({'error': '文件不存在或不属于该项目'}), 404
        return jsonify({'error': '获取项目文件内容失败'}), 500

# Update project file translation content
@files_bp.route('/<file_id>', methods=['PUT'])
def update_project_file_translation(project_id, file_id):
    try:
        data = request.json
        translated_segments_list = data.get('translatedSegments')

        # Basic validation
        if translated_segments_list is None or not isinstance(translated_segments_list, list):
            return jsonify({'error': '缺少或无效的翻译内容格式 (需要列表)'}), 400

        project = Project.query.get_or_404(project_id, description='项目不存在')
        file = File.query.filter_by(id=file_id, project_id=project_id).first_or_404(
             description='文件不存在或不属于该项目'
        )

        # 获取数据库中已排序的段落
        db_segments = file.segments.order_by(Segment.segment_index).all()

        # 验证段落数量是否匹配
        if len(translated_segments_list) != len(db_segments):
             return jsonify({'error': f'翻译段落数量 ({len(translated_segments_list)}) 与原始段落数量 ({len(db_segments)}) 不匹配'}), 400

        # 更新每个 Segment 的 translated_text
        for index, segment_obj in enumerate(db_segments):
            # 检查传入列表对应索引是否存在，以防万一
            if index < len(translated_segments_list):
                 segment_obj.translated_text = translated_segments_list[index]
            else:
                 # 如果传入列表更短（理论上不应发生，因为上面检查过），可以选择报错或跳过
                 current_app.logger.warning(f"传入的翻译列表在索引 {index} 处过短 (File ID: {file_id})")
                 pass # 或者设置为空? segment_obj.translated_text = ''

        project.last_modified = datetime.now()

        # Update file completion rate (模型中的方法已更新)
        file.update_completion_rate()

        # Update project completion rate (模型中的方法已更新)
        project.update_completion_rate()

        db.session.commit()

        return jsonify({
            'message': '翻译内容已更新',
            'completionRate': file.completion_rate,
            'projectCompletionRate': project.completion_rate
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'更新项目文件翻译内容出错 (Project: {project_id}, File: {file_id}): {str(e)}')
        if hasattr(e, 'code') and e.code == 404:
             return jsonify({'error': '项目或文件不存在'}), 404
        return jsonify({'error': '更新项目文件翻译内容失败'}), 500

# Delete a project file
@files_bp.route('/<file_id>', methods=['DELETE'])
def delete_project_file(project_id, file_id):
    try:
        project = Project.query.get_or_404(project_id, description='项目不存在')
        file = File.query.filter_by(id=file_id, project_id=project_id).first_or_404(
             description='文件不存在或不属于该项目'
        )

        file_path = file.file_path # Get path before deleting DB record

        # Delete physical file first
        if file_path and os.path.exists(file_path):
             try:
                 os.remove(file_path)
             except OSError as rm_error:
                 current_app.logger.error(f'删除物理文件时出错 (Path: {file_path}): {str(rm_error)}')
                 # Decide if you want to stop or continue with DB deletion
                 # For now, log and continue

        # Delete file from database
        db.session.delete(file)

        # Update project modification time
        project.last_modified = datetime.now()

        db.session.commit() # Commit deletion and project time update

        # Update project completion rate (after file is deleted)
        project.update_completion_rate()
        db.session.commit() # Commit project rate update

        return jsonify({'message': '文件已从项目中删除'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除项目文件出错 (Project: {project_id}, File: {file_id}): {str(e)}')
        if hasattr(e, 'code') and e.code == 404:
             return jsonify({'error': '项目或文件不存在'}), 404
        return jsonify({'error': '删除项目文件失败'}), 500

# Download translated project file
@files_bp.route('/<file_id>/download', methods=['GET'])
def download_project_file(project_id, file_id):
    temp_path = None # Initialize for potential cleanup
    try:
        # Ensure project exists (optional, depends on file ID uniqueness)
        # Project.query.get_or_404(project_id, description='项目不存在')

        file = File.query.filter_by(id=file_id, project_id=project_id).first_or_404(
             description='文件不存在或不属于该项目'
        )

        # Check if all segments are translated (allow download even if not fully translated?)
        # Current logic requires full translation:
        # all_translated = all(s and s.strip() for s in file.translated_segments_list)
        # if not all_translated:
        #     return jsonify({'error': '翻译尚未完成，无法下载'}), 400
        # Consider allowing partial download if needed. For now, keep original logic.

        # Generate translated file content (use original segment if translation is empty?)
        # 从 Segment 表获取翻译内容
        ordered_segments = file.segments.order_by(Segment.segment_index).all()
        translated_list = [seg.translated_text for seg in ordered_segments]

        # 使用 '\n\n' 作为分隔符
        translated_content = '\n\n'.join(translated_list)

        # Create temporary file for download
        base_name, ext = os.path.splitext(file.file_name)
        download_filename = f"{base_name}-translated{ext}"
        # Use a temporary directory or the DATA_DIR for the temp file
        temp_path = os.path.join(DATA_DIR, f"temp_{file_id}{ext}") # Use unique temp name

        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        return send_file(
            temp_path,
            as_attachment=True,
            download_name=download_filename, # Use the user-friendly name
            mimetype='text/plain'
        )
    except Exception as e:
        current_app.logger.error(f'下载项目文件翻译出错 (Project: {project_id}, File: {file_id}): {str(e)}')
        if hasattr(e, 'code') and e.code == 404:
             return jsonify({'error': '文件不存在或不属于该项目'}), 404
        return jsonify({'error': '下载项目文件翻译失败'}), 500
    finally:
        # Clean up the temporary file after sending or if an error occurred
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as rm_error:
                current_app.logger.error(f'清理下载临时文件时出错: {str(rm_error)}')
