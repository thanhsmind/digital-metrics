import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG_MODE,
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """
    Khởi tạo các cấu hình cần thiết khi khởi động ứng dụng
    """
    # Đảm bảo thư mục token tồn tại
    os.makedirs(settings.TOKEN_STORAGE_DIR, exist_ok=True)

    # Kiểm tra cấu hình Facebook
    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        logging.warning(
            "WARNING: Facebook API credentials are not properly configured. "
            "Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in environment variables."
        )


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Digital Metrics API for analytics integration",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok", "api_version": settings.VERSION}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG_MODE
    )
