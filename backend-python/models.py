from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

# 新增 Segment 模型
class Segment(db.Model):
    """段落模型"""
    id = db.Column(db.Integer, primary_key=True) # 使用自增整数作为主键
    file_id = db.Column(db.String(36), db.ForeignKey('file.id'), nullable=False, index=True) # 外键，加索引
    segment_index = db.Column(db.Integer, nullable=False) # 段落在文件中的顺序
    original_text = db.Column(db.Text, nullable=False)
    translated_text = db.Column(db.Text, nullable=False, default='') # 默认为空字符串

    # 确保 file_id 和 segment_index 组合唯一
    __table_args__ = (db.UniqueConstraint('file_id', 'segment_index', name='_file_segment_uc'),)

    def to_dict(self):
        """转换为字典表示 (主要在File.to_dict中使用)"""
        return {
            'index': self.segment_index,
            'original': self.original_text,
            'translated': self.translated_text
        }


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
                # 使用新的方式计算
                segments_count = file.segments.count() # 查询段落数量
                total_segments += segments_count
                # 查询已翻译段落数量 (使用 with_parent 优化查询)
                completed_segments += Segment.query.with_parent(file).filter(Segment.translated_text != '').count()
            except Exception as e:
                # 考虑日志记录 file.id
                print(f"Error calculating completion rate for file {file.id}: {str(e)}")

        self.completion_rate = round((completed_segments / total_segments) * 100) if total_segments > 0 else 0

class File(db.Model):
    """文件模型"""
    id = db.Column(db.String(36), primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    # 移除旧的 segments 字段
    # original_segments = db.Column(db.Text, nullable=False)
    # translated_segments = db.Column(db.Text, nullable=False)
    completion_rate = db.Column(db.Integer, default=0)

    # 外键
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False)

    # 新增与 Segment 的关系
    # lazy='dynamic' 允许进一步查询, order_by 保证顺序
    segments = db.relationship('Segment', backref='file', lazy='dynamic',
                               cascade="all, delete-orphan",
                               order_by='Segment.segment_index')

    # 移除旧的 @property 方法

    def to_dict(self):
        """转换为字典表示"""
        # 从关系中获取段落
        ordered_segments = self.segments.order_by(Segment.segment_index).all()
        original_list = [seg.original_text for seg in ordered_segments]
        translated_list = [seg.translated_text for seg in ordered_segments]

        return {
            'id': self.id,
            'fileName': self.file_name,
            'filePath': self.file_path, # 考虑是否真的需要暴露完整路径给前端
            'uploadDate': self.upload_date.isoformat(),
            'originalSegments': original_list,
            'translatedSegments': translated_list,
            'completionRate': self.completion_rate
        }

    def update_completion_rate(self):
        """更新文件完成率"""
        try:
            # 使用新的方式计算
            total_segments = self.segments.count()
            if total_segments == 0:
                self.completion_rate = 0
                return

            completed_segments = self.segments.filter(Segment.translated_text != '').count()
            self.completion_rate = round((completed_segments / total_segments) * 100)

        except Exception as e:
            print(f"Error updating file completion rate (File ID: {self.id}): {str(e)}")
            self.completion_rate = 0
