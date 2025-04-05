from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Project(db.Model):
    """项目模型"""
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completion_rate = db.Column(db.Integer, default=0)
    
    # 关联关系
    files = db.relationship('File', backref='project', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'creationDate': self.creation_date.isoformat(),
            'lastModified': self.last_modified.isoformat(),
            'files': [file.to_dict() for file in self.files],
            'completionRate': self.completion_rate
        }
    
    def update_completion_rate(self):
        """更新项目完成率"""
        if not self.files:
            self.completion_rate = 0
            return
        
        total_segments = 0
        completed_segments = 0
        
        for file in self.files:
            try:
                segments = len(file.original_segments_list)
                total_segments += segments
                completed_segments += sum(1 for s in file.translated_segments_list if s.strip())
            except Exception as e:
                print(f"Error calculating completion rate: {str(e)}")
        
        self.completion_rate = round((completed_segments / total_segments) * 100) if total_segments > 0 else 0

class File(db.Model):
    """文件模型"""
    id = db.Column(db.String(36), primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    original_segments = db.Column(db.Text, nullable=False)  # 存储为JSON字符串
    translated_segments = db.Column(db.Text, nullable=False)  # 存储为JSON字符串
    completion_rate = db.Column(db.Integer, default=0)
    
    # 外键
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False)
    
    @property
    def original_segments_list(self):
        """获取原始段落列表"""
        return json.loads(self.original_segments)
    
    @original_segments_list.setter
    def original_segments_list(self, segments):
        """设置原始段落列表"""
        self.original_segments = json.dumps(segments, ensure_ascii=False)
    
    @property
    def translated_segments_list(self):
        """获取翻译段落列表"""
        return json.loads(self.translated_segments)
    
    @translated_segments_list.setter
    def translated_segments_list(self, segments):
        """设置翻译段落列表"""
        self.translated_segments = json.dumps(segments, ensure_ascii=False)
    
    def to_dict(self):
        """转换为字典表示"""
        return {
            'id': self.id,
            'fileName': self.file_name,
            'filePath': self.file_path,
            'uploadDate': self.upload_date.isoformat(),
            'originalSegments': self.original_segments_list,
            'translatedSegments': self.translated_segments_list,
            'completionRate': self.completion_rate
        }
    
    def update_completion_rate(self):
        """更新文件完成率"""
        try:
            original = self.original_segments_list
            translated = self.translated_segments_list
            
            total_segments = len(original)
            completed_segments = sum(1 for s in translated if s.strip())
            
            self.completion_rate = round((completed_segments / total_segments) * 100) if total_segments > 0 else 0
        except Exception as e:
            print(f"Error updating file completion rate: {str(e)}")
            self.completion_rate = 0
