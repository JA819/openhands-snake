from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.requests import Request
import uvicorn
import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import aiofiles
from pathlib import Path

# 导入业务逻辑模块
from modules.qa_generator import QAGenerator
from modules.agent_tester import AgentTester
from modules.similarity_scorer import SimilarityScorer
from modules.task_manager import TaskManager
from modules.file_manager import FileManager
from modules.database import Database

app = FastAPI(title="智能体评估系统", description="智能体API导入、问答对生成、相似度评分系统")

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 创建必要的目录
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# 初始化组件
db = Database()
task_manager = TaskManager()
file_manager = FileManager()

# 全局变量存储智能体配置
agents_config = {}

# 在文件开头添加默认API密钥配置
QA_GENERATION_API_KEY = "sk-..."  # 问答生成模型API密钥
SIMILARITY_API_KEY = "sk-..."     # 相似度计算模型API密钥

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    try:
        await db.init_db()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")

# ==================== 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    """智能体API导入页面"""
    return templates.TemplateResponse("agents.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """系统仪表盘页面"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/pipeline", response_class=HTMLResponse)
async def pipeline_page(request: Request):
    """完整流水线处理页面"""
    return templates.TemplateResponse("pipeline.html", {"request": request})

@app.get("/qa-generation", response_class=HTMLResponse)
async def qa_generation_page(request: Request):
    """问答对生成页面"""
    return templates.TemplateResponse("qa_generation.html", {"request": request})

@app.get("/dify-test", response_class=HTMLResponse)
async def dify_test_page(request: Request):
    """Dify工作流测试页面"""
    return templates.TemplateResponse("dify_test.html", {"request": request})

@app.get("/similarity", response_class=HTMLResponse)
async def similarity_page(request: Request):
    """相似度评分页面"""
    return templates.TemplateResponse("similarity.html", {"request": request})

@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """结果分析页面"""
    return templates.TemplateResponse("analysis.html", {"request": request})

@app.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    """文件管理页面"""
    return templates.TemplateResponse("files.html", {"request": request})

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """任务管理页面"""
    return templates.TemplateResponse("tasks.html", {"request": request})

# ==================== API路由 ====================

@app.post("/api/agents/config")
async def configure_agents(
    agent_count: int = Form(...),
    agent1_url: str = Form(None),
    agent1_key: str = Form(None),
    agent2_url: str = Form(None),
    agent2_key: str = Form(None),
    agent3_url: str = Form(None),
    agent3_key: str = Form(None)
):
    """配置智能体"""
    global agents_config
    agents_config = {"count": agent_count}
    
    if agent_count >= 1 and agent1_url and agent1_key:
        agents_config["agent1"] = {"url": agent1_url, "key": agent1_key}
    if agent_count >= 2 and agent2_url and agent2_key:
        agents_config["agent2"] = {"url": agent2_url, "key": agent2_key}
    if agent_count >= 3 and agent3_url and agent3_key:
        agents_config["agent3"] = {"url": agent3_url, "key": agent3_key}
    
    return {"status": "success", "message": "智能体配置成功"}

@app.get("/api/agents/status")
async def get_agents_status():
    """获取智能体状态"""
    if not agents_config:
        return {"configured": False, "agents": []}
    
    agents_status = []
    for i in range(1, agents_config["count"] + 1):
        agent_key = f"agent{i}"
        if agent_key in agents_config:
            # 测试连接
            try:
                tester = AgentTester()
                status = await tester.test_connection(
                    agents_config[agent_key]["url"],
                    agents_config[agent_key]["key"]
                )
                agents_status.append({
                    "name": f"智能体{i}",
                    "status": "connected" if status else "failed",
                    "url": agents_config[agent_key]["url"]
                })
            except:
                agents_status.append({
                    "name": f"智能体{i}",
                    "status": "failed",
                    "url": agents_config[agent_key]["url"]
                })
    
    return {"configured": True, "agents": agents_status}

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """获取仪表盘统计信息"""
    stats = await db.get_dashboard_stats()
    return stats

# 修改问答生成API端点
@app.post("/api/qa/generate")
async def generate_qa_pairs(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    max_paragraphs: int = Form(20),
    temperature: float = Form(0.3)
):
    """生成问答对"""
    task_id = str(uuid.uuid4())
    
    # 保存上传的文件
    file_paths = []
    for file in files:
        file_path = f"uploads/{task_id}_{file.filename}"
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        file_paths.append(file_path)
    
    # 创建任务
    await db.create_task(task_id, "qa_generation", "pending", {
        "files": file_paths,
        "max_paragraphs": max_paragraphs,
        "temperature": temperature
    })
    
    # 后台执行任务,使用默认API密钥
    background_tasks.add_task(
        execute_qa_generation,
        task_id, file_paths, max_paragraphs, temperature, QA_GENERATION_API_KEY
    )
    
    return {"task_id": task_id, "status": "started"}

async def execute_qa_generation(task_id: str, file_paths: List[str], max_paragraphs: int, temperature: float, api_key: str):
    """执行问答对生成任务"""
    try:
        await db.update_task_status(task_id, "running")
        
        generator = QAGenerator(api_key)
        output_path = f"outputs/qa_pairs_{task_id}.xlsx"
        
        result = await generator.process_documents(file_paths, output_path, max_paragraphs, temperature)
        
        await db.update_task_status(task_id, "completed", {
            "output_file": output_path,
            "qa_count": len(result)
        })
        
    except Exception as e:
        await db.update_task_status(task_id, "failed", {"error": str(e)})

@app.post("/api/dify/test")
async def test_dify_workflow(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    temperature: float = Form(0.3),
    delay: int = Form(1)
):
    """测试Dify工作流"""
    if not agents_config:
        raise HTTPException(status_code=400, detail="请先配置智能体")
    
    task_id = str(uuid.uuid4())
    
    # 保存上传的文件
    file_paths = []
    for file in files:
        file_path = f"uploads/{task_id}_{file.filename}"
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        file_paths.append(file_path)
    
    # 创建任务
    await db.create_task(task_id, "dify_test", "pending", {
        "files": file_paths,
        "temperature": temperature,
        "delay": delay
    })
    
    # 后台执行任务
    background_tasks.add_task(
        execute_dify_test,
        task_id, file_paths, temperature, delay
    )
    
    return {"task_id": task_id, "status": "started"}

async def execute_dify_test(task_id: str, file_paths: List[str], temperature: float, delay: int):
    """执行Dify测试任务"""
    try:
        await db.update_task_status(task_id, "running")
        
        tester = AgentTester()
        output_path = f"outputs/dify_test_{task_id}.xlsx"
        
        result = await tester.test_agents(agents_config, file_paths, output_path, delay)
        
        await db.update_task_status(task_id, "completed", {
            "output_file": output_path,
            "test_count": result
        })
        
    except Exception as e:
        await db.update_task_status(task_id, "failed", {"error": str(e)})

# 修改相似度计算API端点 
@app.post("/api/similarity/calculate")
async def calculate_similarity(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """计算相似度评分"""
    task_id = str(uuid.uuid4())
    
    # 保存上传的文件
    file_path = f"uploads/{task_id}_{file.filename}"
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # 创建任务
    await db.create_task(task_id, "similarity_calculation", "pending", {
        "input_file": file_path
    })
    
    # 后台执行任务,使用默认API密钥
    background_tasks.add_task(
        execute_similarity_calculation,
        task_id, file_path, SIMILARITY_API_KEY
    )
    
    return {"task_id": task_id, "status": "started"}

async def execute_similarity_calculation(task_id: str, file_path: str, api_key: str):
    """执行相似度计算任务"""
    try:
        await db.update_task_status(task_id, "running")
        
        scorer = SimilarityScorer(api_key)
        output_path = f"outputs/similarity_scores_{task_id}.xlsx"
        
        result = await scorer.calculate_scores(file_path, output_path)
        
        await db.update_task_status(task_id, "completed", {
            "output_file": output_path,
            "scores": result
        })
        
    except Exception as e:
        await db.update_task_status(task_id, "failed", {"error": str(e)})

# 修改完整流水线API端点
@app.post("/api/pipeline/start")
async def start_full_pipeline(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    max_paragraphs: int = Form(20),
    temperature: float = Form(0.3),
    delay: int = Form(1)
):
    """启动完整流水线"""
    if not agents_config:
        raise HTTPException(status_code=400, detail="请先配置智能体")
    
    task_id = str(uuid.uuid4())
    
    # 保存上传的文件
    file_paths = []
    for file in files:
        file_path = f"uploads/{task_id}_{file.filename}"
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        file_paths.append(file_path)
    
    # 创建任务
    await db.create_task(task_id, "full_pipeline", "pending", {
        "files": file_paths,
        "max_paragraphs": max_paragraphs,
        "temperature": temperature,
        "delay": delay
    })
    
    # 后台执行任务,使用默认API密钥
    background_tasks.add_task(
        execute_full_pipeline,
        task_id, file_paths, max_paragraphs, temperature, delay, 
        QA_GENERATION_API_KEY, SIMILARITY_API_KEY
    )
    
    return {"task_id": task_id, "status": "started"}

async def execute_full_pipeline(task_id: str, file_paths: List[str], max_paragraphs: int, temperature: float, delay: int, qa_api_key: str, similarity_api_key: str):
    """执行完整流水线任务"""
    try:
        await db.update_task_status(task_id, "running", {"step": "生成问答对"})
        
        # 步骤1: 生成问答对
        generator = QAGenerator(qa_api_key)
        qa_output = f"outputs/qa_pairs_{task_id}.xlsx"
        qa_result = await generator.process_documents(file_paths, qa_output, max_paragraphs, temperature)
        
        await db.update_task_status(task_id, "running", {"step": "测试智能体"})
        
        # 步骤2: 测试智能体
        tester = AgentTester()
        test_output = f"outputs/dify_test_{task_id}.xlsx"
        test_result = await tester.test_agents_with_qa_file(agents_config, qa_output, test_output, delay)
        
        await db.update_task_status(task_id, "running", {"step": "计算相似度"})
        
        # 步骤3: 计算相似度
        scorer = SimilarityScorer(similarity_api_key)
        similarity_output = f"outputs/similarity_scores_{task_id}.xlsx"
        similarity_result = await scorer.calculate_scores(test_output, similarity_output)
        
        await db.update_task_status(task_id, "completed", {
            "qa_file": qa_output,
            "test_file": test_output,
            "similarity_file": similarity_output,
            "qa_count": len(qa_result),
            "test_count": test_result,
            "scores": similarity_result
        })
        
    except Exception as e:
        await db.update_task_status(task_id, "failed", {"error": str(e)})

@app.get("/api/tasks")
async def get_tasks():
    """获取任务列表"""
    tasks = await db.get_tasks()
    return tasks

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """获取任务详情"""
    task = await db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    await db.delete_task(task_id)
    return {"status": "success", "message": "任务已删除"}

@app.get("/api/files")
async def get_files():
    """获取文件列表"""
    files = file_manager.get_output_files()
    return files

@app.get("/api/files/{filename}")
async def download_file(filename: str):
    """下载文件"""
    file_path = f"outputs/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, filename=filename)

@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """删除文件"""
    file_path = f"outputs/{filename}"
    if os.path.exists(file_path):
        os.remove(file_path)
    return {"status": "success", "message": "文件已删除"}

@app.get("/api/analysis/files")
async def get_analysis_files():
    """获取可分析的文件列表"""
    files = file_manager.get_similarity_files()
    return files

@app.get("/api/analysis/{filename}")
async def get_analysis_data(filename: str):
    """获取分析数据"""
    file_path = f"outputs/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 解析Excel文件并返回分析数据
    from modules.analyzer import Analyzer
    analyzer = Analyzer()
    analysis_data = await analyzer.analyze_file(file_path)
    return analysis_data

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",  # 修改这里
        port=12000,
        reload=True,
        reload_dirs=["./"]
    )