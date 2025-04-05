import os
import shutil
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from models import db, Project, File
from config import PROJECTS_DIR

# Create a Blueprint for project routes
projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

# Get all projects
@projects_bp.route('', methods=['GET'])
def get_projects():
    try:
        projects = Project.query.all()
        return jsonify([project.to_dict() for project in projects])
    except Exception as e:
        current_app.logger.error(f'获取项目列表出错: {str(e)}')
        return jsonify({'error': '获取项目列表失败'}), 500

# Create a new project
@projects_bp.route('', methods=['POST'])
def create_project():
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')

        if not name:
            return jsonify({'error': '缺少项目名称'}), 400

        project_id = str(uuid.uuid4())
        now = datetime.now()

        # Create project directory
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        project_files_dir = os.path.join(project_dir, 'files')

        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(project_files_dir, exist_ok=True)

        # Create new project instance
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
        current_app.logger.error(f'创建项目出错: {str(e)}')
        # Attempt to clean up directory if creation failed mid-way
        project_dir = os.path.join(PROJECTS_DIR, project_id)
        if os.path.exists(project_dir):
             try:
                 shutil.rmtree(project_dir)
             except OSError as rm_error:
                 current_app.logger.error(f'创建项目失败后清理目录时出错: {str(rm_error)}')
        return jsonify({'error': '创建项目失败'}), 500

# Get specific project details
@projects_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    try:
        project = Project.query.get_or_404(project_id, description='项目不存在')
        return jsonify(project.to_dict())
    except Exception as e:
        # Catch potential errors during serialization or other issues
        current_app.logger.error(f'获取项目详情出错 (ID: {project_id}): {str(e)}')
        # Check if it was a 404 error specifically
        if hasattr(e, 'code') and e.code == 404:
             return jsonify({'error': '项目不存在'}), 404
        return jsonify({'error': '获取项目详情失败'}), 500


# Update project information
@projects_bp.route('/<project_id>', methods=['PUT'])
def update_project(project_id):
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description')

        project = Project.query.get_or_404(project_id, description='项目不存在')

        # Update project information
        if name:
            project.name = name

        # Allow setting description to empty string
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
        current_app.logger.error(f'更新项目信息出错 (ID: {project_id}): {str(e)}')
        if hasattr(e, 'code') and e.code == 404:
             return jsonify({'error': '项目不存在'}), 404
        return jsonify({'error': '更新项目信息失败'}), 500

# Delete project
@projects_bp.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    try:
        project = Project.query.get_or_404(project_id, description='项目不存在')

        project_dir = os.path.join(PROJECTS_DIR, project_id)

        # Delete project directory and files first
        if os.path.exists(project_dir):
            try:
                shutil.rmtree(project_dir)
            except OSError as rm_error:
                 current_app.logger.error(f'删除项目目录时出错 (ID: {project_id}): {str(rm_error)}')
                 # Decide if you want to proceed with DB deletion or return error
                 # For now, log the error and proceed with DB deletion

        # Delete from database (cascades to files due to model definition)
        db.session.delete(project)
        db.session.commit()

        return jsonify({'message': '项目已删除'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除项目出错 (ID: {project_id}): {str(e)}')
        if hasattr(e, 'code') and e.code == 404:
             return jsonify({'error': '项目不存在'}), 404
        return jsonify({'error': '删除项目失败'}), 500
