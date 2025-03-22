# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.connection import init_db
from app.routes import auth, emails  # 导入所有路由模块

# 创建FastAPI应用实例
app = FastAPI(
    title="Email Processing Platform",
    description="智能邮件处理系统API文档",
    version="0.1.0",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "用户认证相关接口"
        },
        {
            "name": "Emails",
            "description": "邮件操作相关接口"
        }
    ]
)

# 配置CORS跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库初始化（异步）
@app.on_event("startup")
async def startup_db_client():
    await init_db()
    print("数据库连接已建立")

@app.on_event("shutdown")
async def shutdown_db_client():
    print("数据库连接已关闭")

# 注册路由模块
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    emails.router,
    prefix="/api/emails",
    tags=["Emails"]
)

# 开发模式下运行（可选）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )