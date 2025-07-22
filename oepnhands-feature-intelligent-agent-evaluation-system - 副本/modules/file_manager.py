import os
import shutil
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

class FileManager:
    def __init__(self):
        self.upload_dir = "uploads"
        self.output_dir = "outputs"
        
        # 确保目录存在
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def get_output_files(self) -> List[Dict[str, Any]]:
        """获取输出文件列表"""
        files = []
        
        if os.path.exists(self.output_dir):
            for filename in os.listdir(self.output_dir):
                file_path = os.path.join(self.output_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        "name": filename,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": self._get_file_type(filename)
                    })
        
        # 按修改时间排序
        files.sort(key=lambda x: x["modified_at"], reverse=True)
        return files

    def get_similarity_files(self) -> List[Dict[str, Any]]:
        """获取相似度评分文件列表"""
        files = self.get_output_files()
        # 过滤出相似度评分文件
        similarity_files = [
            f for f in files 
            if "similarity" in f["name"].lower() or "score" in f["name"].lower()
        ]
        return similarity_files

    def delete_file(self, filename: str) -> bool:
        """删除文件"""
        file_path = os.path.join(self.output_dir, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False

    def get_file_path(self, filename: str) -> str:
        """获取文件完整路径"""
        return os.path.join(self.output_dir, filename)

    def file_exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(os.path.join(self.output_dir, filename))

    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """获取文件详细信息"""
        file_path = os.path.join(self.output_dir, filename)
        
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        return {
            "name": filename,
            "path": file_path,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "type": self._get_file_type(filename)
        }

    def _get_file_type(self, filename: str) -> str:
        """根据文件名获取文件类型"""
        ext = Path(filename).suffix.lower()
        
        type_mapping = {
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.docx': 'word',
            '.doc': 'word',
            '.pdf': 'pdf',
            '.txt': 'text',
            '.json': 'json',
            '.csv': 'csv'
        }
        
        return type_mapping.get(ext, 'unknown')

    def clean_old_files(self, days: int = 7):
        """清理旧文件"""
        current_time = datetime.now()
        
        for directory in [self.upload_dir, self.output_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if (current_time - file_time).days > days:
                            try:
                                os.remove(file_path)
                                print(f"已删除旧文件: {filename}")
                            except Exception as e:
                                print(f"删除文件失败 {filename}: {e}")

    def get_disk_usage(self) -> Dict[str, Any]:
        """获取磁盘使用情况"""
        upload_size = self._get_directory_size(self.upload_dir)
        output_size = self._get_directory_size(self.output_dir)
        
        return {
            "upload_dir_size": upload_size,
            "output_dir_size": output_size,
            "total_size": upload_size + output_size
        }

    def _get_directory_size(self, directory: str) -> int:
        """获取目录大小"""
        total_size = 0
        if os.path.exists(directory):
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        return total_size