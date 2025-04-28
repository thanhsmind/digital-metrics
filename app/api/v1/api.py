from fastapi import APIRouter

from app.api.v1.endpoints import auth, facebook

# Tạm thời tắt Google Ads client
# from app.api.v1.endpoints import google

api_router = APIRouter()
api_router.include_router(
    facebook.router, prefix="/facebook", tags=["facebook"]
)
# Tạm thời tắt Google Ads client
# api_router.include_router(google.router, prefix="/google", tags=["google"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
