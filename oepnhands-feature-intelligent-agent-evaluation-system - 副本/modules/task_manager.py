import asyncio
from typing import Dict, Any, Callable
from datetime import datetime
import uuid

class TaskManager:
    def __init__(self):
        self.running_tasks = {}
        self.task_results = {}

    async def create_task(self, task_type: str, task_func: Callable, *args, **kwargs) -> str:
        """创建并启动任务"""
        task_id = str(uuid.uuid4())
        
        # 创建任务
        task = asyncio.create_task(self._run_task(task_id, task_func, *args, **kwargs))
        
        self.running_tasks[task_id] = {
            "task": task,
            "type": task_type,
            "status": "running",
            "created_at": datetime.now(),
            "progress": 0
        }
        
        return task_id

    async def _run_task(self, task_id: str, task_func: Callable, *args, **kwargs):
        """运行任务的内部方法"""
        try:
            result = await task_func(*args, **kwargs)
            self.running_tasks[task_id]["status"] = "completed"
            self.task_results[task_id] = {"status": "success", "result": result}
        except Exception as e:
            self.running_tasks[task_id]["status"] = "failed"
            self.task_results[task_id] = {"status": "error", "error": str(e)}
        finally:
            # 清理运行中的任务
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id in self.running_tasks:
            return self.running_tasks[task_id]
        elif task_id in self.task_results:
            return self.task_results[task_id]
        else:
            return {"status": "not_found"}

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]["task"]
            task.cancel()
            self.running_tasks[task_id]["status"] = "cancelled"
            return True
        return False

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        all_tasks = {}
        all_tasks.update(self.running_tasks)
        all_tasks.update(self.task_results)
        return all_tasks

    def update_task_progress(self, task_id: str, progress: int):
        """更新任务进度"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["progress"] = progress