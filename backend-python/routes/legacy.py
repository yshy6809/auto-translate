import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from ..models import db, Project, File, LegacyFile
from ..utils import parse_file_content
from ..config import PROJECTS_DIR, DATA_DIR

# Create a Blueprint for legacy file routes
legacy_bp = Blueprint('legacy', __name__, url_prefix='/api/files')

# Helper function to ensure default project exists
def ensure_default_project():
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
        # Create default project directory
        project_dir = os.path.join(PROJECTS_DIR, default_project_id)
        project_files_dir = os.path.join(project_dir, 'files')
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(project_files_dir, exist_ok=True)
        # Commit here to ensure project exists before file operations
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'创建默认项目时出错: {str(e)}')
            raise  # Re-raise the exception to be caught by the route handler
    return default_project

# Get all files (legacy view - combines LegacyFile and File)
@legacy_bp.route('', methods=['GET'])
def get_files():
    try:
        # Get legacy files
        legacy_files = LegacyFile.query.all()
        legacy_file_dicts = [file.to_dict() for file in legacy_files]
        legacy_file_ids = {f['id'] for f in legacy_file_dicts} # Keep track of IDs

        # Get project files, adding project info, excluding duplicates found in legacy
        project_files = []
        projects = Project.query.all()
        for project in projects:
            files = File.query.filter_by(project_id=project.id).all()
            for file in files:
                if file.id not in legacy_file_ids: # Avoid duplicates if synced
                    file_dict = file.to_dict()
                    file_dict['projectId'] = project.id
                    file_dict['projectName'] = project.name
                    project_files.append(file_dict)

        # Combine results (legacy first, then new ones)
        all_files = legacy_file_dicts + project_files
        return jsonify(all_files)
    except Exception as e:
        current_app.logger.error(f'获取旧版文件列表出错: {str(e)}')
        return jsonify({'error': '获取文件列表失败'}), 500

# Upload new file (legacy - creates/uses default project)
@legacy_bp.route('', methods=['POST'])
def upload_file():
    file_path = None # Initialize for potential cleanup
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400

        # Ensure default project exists
        default_project = ensure_default_project()
        project_files_dir = os.path.join(PROJECTS_DIR, default_project.id, 'files')
        os.makedirs(project_files_dir, exist_ok=True) # Ensure dir exists

        # Generate unique filename
        file_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        _, file_extension = os.path.splitext(original_filename)
        if not file_extension:
             file_extension = '.txt' # Default extension
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(project_files_dir, filename)

        # Save file
        file.save(file_path)

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as read_err:
             os.remove(file_path) # Clean up
             current_app.logger.error(f'读取旧版上传文件时出错: {str(read_err)}')
             return jsonify({'error': '读取文件内容时出错'}), 500

        original_segments = parse_file_content(file_content)
        if not original_segments:
             os.remove(file_path) # Clean up
             return jsonify({'error': '文件内容为空或无法解析'}), 400

        # Create Project File record
        new_file = File(
            id=file_id,
            file_name=original_filename,
            file_path=file_path,
            upload_date=datetime.now(),
            project_id=default_project.id,
            completion_rate=0
        )
        new_file.original_segments_list = original_segments
        new_file.translated_segments_list = [''] * len(original_segments)
        db.session.add(new_file)

        # Create Legacy File record for compatibility
        legacy_file = LegacyFile(
            id=file_id,
            file_name=original_filename,
            file_path=file_path,
            upload_date=datetime.now(),
            completion_rate=0,
            project_id=default_project.id, # Link legacy record too
            project_name=default_project.name
        )
        legacy_file.original_segments_list = original_segments
        legacy_file.translated_segments_list = [''] * len(original_segments)
        db.session.add(legacy_file)

        # Update project modification time
        default_project.last_modified = datetime.now()

        db.session.commit() # Commit both files and project time

        # Update project completion rate
        default_project.update_completion_rate()
        db.session.commit() # Commit rate update

        return jsonify({
            'id': file_id,
            'projectId': default_project.id, # Return project ID
            'message': '文件上传成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'旧版上传文件出错: {str(e)}')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as rm_error:
                 current_app.logger.error(f'旧版上传失败后清理文件时出错: {str(rm_error)}')
        return jsonify({'error': '上传文件失败'}), 500

# Get specific file content (legacy - checks LegacyFile then File)
@legacy_bp.route('/<file_id>', methods=['GET'])
def get_file(file_id):
    try:
        # Prioritize LegacyFile table for this endpoint
        legacy_file = LegacyFile.query.get(file_id)
        if legacy_file:
            return jsonify(legacy_file.to_dict())

        # Fallback to File table if not in LegacyFile
        file = File.query.get(file_id)
        if file:
            project = Project.query.get(file.project_id) # Get project info
            file_dict = file.to_dict()
            if project:
                file_dict['projectId'] = project.id
                file_dict['projectName'] = project.name
            else: # Handle case where project might be missing (data inconsistency)
                 file_dict['projectId'] = file.project_id
                 file_dict['projectName'] = '未知项目'
            return jsonify(file_dict)

        return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        current_app.logger.error(f'旧版获取文件内容出错 (ID: {file_id}): {str(e)}')
        return jsonify({'error': '获取文件内容失败'}), 500

# Update file translation (legacy - updates both tables if possible)
@legacy_bp.route('/<file_id>', methods=['PUT'])
def update_file_translation(file_id):
    try:
        data = request.json
        translated_segments = data.get('translatedSegments')

        if translated_segments is None or not isinstance(translated_segments, list):
            return jsonify({'error': '缺少或无效的翻译内容格式'}), 400

        # Try updating LegacyFile first
        legacy_file = LegacyFile.query.get(file_id)
        file_updated = False
        project_rate = None

        if legacy_file:
            # Validate segment count for legacy file
            if len(translated_segments) != len(legacy_file.original_segments_list):
                 return jsonify({'error': f'翻译段落数量与旧记录不匹配'}), 400

            legacy_file.translated_segments_list = translated_segments
            legacy_file.update_completion_rate() # Update legacy completion rate
            file_updated = True

            # Sync with Project/File if linked
            if legacy_file.project_id:
                file = File.query.filter_by(id=file_id, project_id=legacy_file.project_id).first()
                if file:
                    # Double check segment count before updating the main File record
                    if len(translated_segments) == len(file.original_segments_list):
                        file.translated_segments_list = translated_segments
                        file.update_completion_rate()
                        project = Project.query.get(file.project_id)
                        if project:
                            project.last_modified = datetime.now()
                            project.update_completion_rate()
                            project_rate = project.completion_rate
                    else:
                         current_app.logger.warning(f"旧版更新时段落数不匹配 (File ID: {file_id}) - Project File 未同步更新")


        # If not found in LegacyFile, try updating File directly
        if not file_updated:
            file = File.query.get(file_id)
            if file:
                 # Validate segment count for file
                 if len(translated_segments) != len(file.original_segments_list):
                     return jsonify({'error': f'翻译段落数量与记录不匹配'}), 400

                 file.translated_segments_list = translated_segments
                 file.update_completion_rate()
                 project = Project.query.get(file.project_id)
                 if project:
                     project.last_modified = datetime.now()
                     project.update_completion_rate()
                     project_rate = project.completion_rate
                 file_updated = True
            else:
                 return jsonify({'error': '文件不存在'}), 404 # Not found in either table

        db.session.commit()

        # Determine which completion rate to return
        final_completion_rate = legacy_file.completion_rate if legacy_file else file.completion_rate

        response = {'message': '翻译内容已更新', 'completionRate': final_completion_rate}
        if project_rate is not None:
             response['projectCompletionRate'] = project_rate

        return jsonify(response)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'旧版更新翻译内容出错 (ID: {file_id}): {str(e)}')
        return jsonify({'error': '更新翻译内容失败'}), 500


# Delete file (legacy - deletes from both tables and filesystem)
@legacy_bp.route('/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    try:
        legacy_file = LegacyFile.query.get(file_id)
        file = File.query.get(file_id) # Also check the main File table

        if not legacy_file and not file:
            return jsonify({'error': '文件不存在'}), 404

        file_path = None
        project_id_to_update = None

        # Get info primarily from legacy_file if it exists
        if legacy_file:
            file_path = legacy_file.file_path
            project_id_to_update = legacy_file.project_id
            db.session.delete(legacy_file)

        # If file exists in main table (even if not in legacy), ensure it's deleted
        if file:
            if not file_path: # Get path from File if not found in LegacyFile
                 file_path = file.file_path
            if not project_id_to_update: # Get project ID if not found in LegacyFile
                 project_id_to_update = file.project_id
            db.session.delete(file)

        # Delete physical file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as rm_error:
                current_app.logger.error(f'旧版删除物理文件时出错 (Path: {file_path}): {str(rm_error)}')
                # Log and continue with DB operation

        # Update project if a project was associated
        if project_id_to_update:
            project = Project.query.get(project_id_to_update)
            if project:
                project.last_modified = datetime.now()
                # Commit deletion and time update first
                db.session.commit()
                # Then update rate
                project.update_completion_rate()
                db.session.commit()
            else:
                 # Commit deletions even if project not found
                 db.session.commit()
        else:
            # Commit deletions if no project was linked
            db.session.commit()

        return jsonify({'message': '文件已删除'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'旧版删除文件出错 (ID: {file_id}): {str(e)}')
        return jsonify({'error': '删除文件失败'}), 500

# Download translated file (legacy)
@legacy_bp.route('/<file_id>/download', methods=['GET'])
def download_file(file_id):
    temp_path = None
    try:
        # Prioritize LegacyFile
        legacy_file = LegacyFile.query.get(file_id)
        file_to_download = None
        filename_base = "download"

        if legacy_file:
            file_to_download = legacy_file
            filename_base, ext = os.path.splitext(legacy_file.file_name)
        else:
            # Fallback to File table
            file = File.query.get(file_id)
            if file:
                file_to_download = file
                filename_base, ext = os.path.splitext(file.file_name)
            else:
                return jsonify({'error': '文件不存在'}), 404

        # Check translation status (optional: allow partial download?)
        # all_translated = all(s and s.strip() for s in file_to_download.translated_segments_list)
        # if not all_translated:
        #     return jsonify({'error': '翻译尚未完成'}), 400

        translated_content = '\n\n'.join(file_to_download.translated_segments_list)

        # Create temporary file
        _, file_extension = os.path.splitext(file_to_download.file_name)
        if not file_extension: file_extension = ".txt" # Default extension
        download_filename = f"{filename_base}-translated{file_extension}"
        temp_path = os.path.join(DATA_DIR, f"temp_legacy_{file_id}{file_extension}")

        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        return send_file(
            temp_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='text/plain'
        )
    except Exception as e:
        current_app.logger.error(f'旧版下载翻译文件出错 (ID: {file_id}): {str(e)}')
        return jsonify({'error': '下载翻译文件失败'}), 500
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as rm_error:
                current_app.logger.error(f'清理旧版下载临时文件时出错: {str(rm_error)}')
