import sqlite3
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiosqlite

class Database:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path

    async def init_db(self):
        """初始化数据库"""
        async with aiosqlite.connect(self.db_path) as db:
            # 创建任务表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parameters TEXT,
                    result TEXT
                )
            """)
            
            # 创建系统状态表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()

    async def create_task(self, task_id: str, task_type: str, status: str, parameters: Dict = None):
        """创建任务"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO tasks (id, type, status, parameters) VALUES (?, ?, ?, ?)",
                (task_id, task_type, status, json.dumps(parameters) if parameters else None)
            )
            await db.commit()

    async def update_task_status(self, task_id: str, status: str, result: Dict = None):
        """更新任务状态"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tasks SET status = ?, result = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, json.dumps(result) if result else None, task_id)
            )
            await db.commit()

    async def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务详情"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "type": row[1],
                        "status": row[2],
                        "created_at": row[3],
                        "updated_at": row[4],
                        "parameters": json.loads(row[5]) if row[5] else {},
                        "result": json.loads(row[6]) if row[6] else {}
                    }
                return None

    async def get_tasks(self, limit: int = 50) -> List[Dict]:
        """获取任务列表"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                tasks = []
                for row in rows:
                    tasks.append({
                        "id": row[0],
                        "type": row[1],
                        "status": row[2],
                        "created_at": row[3],
                        "updated_at": row[4],
                        "parameters": json.loads(row[5]) if row[5] else {},
                        "result": json.loads(row[6]) if row[6] else {}
                    })
                return tasks

    async def delete_task(self, task_id: str):
        """删除任务"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await db.commit()

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取仪表盘统计信息"""
        async with aiosqlite.connect(self.db_path) as db:
            # 任务统计
            async with db.execute(
                "SELECT status, COUNT(*) FROM tasks GROUP BY status"
            ) as cursor:
                status_counts = dict(await cursor.fetchall())
            
            # 任务类型统计
            async with db.execute(
                "SELECT type, COUNT(*) FROM tasks GROUP BY type"
            ) as cursor:
                type_counts = dict(await cursor.fetchall())
            
            # 最近任务
            async with db.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT 5"
            ) as cursor:
                recent_tasks = []
                rows = await cursor.fetchall()
                for row in rows:
                    recent_tasks.append({
                        "id": row[0],
                        "type": row[1],
                        "status": row[2],
                        "created_at": row[3]
                    })
            
            # 总任务数
            async with db.execute("SELECT COUNT(*) FROM tasks") as cursor:
                total_tasks = (await cursor.fetchone())[0]
            
            return {
                "total_tasks": total_tasks,
                "status_counts": status_counts,
                "type_counts": type_counts,
                "recent_tasks": recent_tasks
            }

    async def update_system_status(self, component: str, status: str, message: str = None):
        """更新系统状态"""
        async with aiosqlite.connect(self.db_path) as db:
            # 先删除旧记录
            await db.execute("DELETE FROM system_status WHERE component = ?", (component,))
            # 插入新记录
            await db.execute(
                "INSERT INTO system_status (component, status, message) VALUES (?, ?, ?)",
                (component, status, message)
            )
            await db.commit()

    async def get_system_status(self) -> List[Dict]:
        """获取系统状态"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT component, status, message, updated_at FROM system_status ORDER BY updated_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "component": row[0],
                        "status": row[1],
                        "message": row[2],
                        "updated_at": row[3]
                    }
                    for row in rows
                ]