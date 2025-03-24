from fastapi import FastAPI
from app.routes.health_check import health_check_router
from app.routes.realtime import realtime_router
from app.routes.mbti import router as mbti_router
from app.routes.ocean import router as ocean_router


app = FastAPI()

# Registering routers
app.include_router(health_check_router)
app.include_router(realtime_router)
app.include_router(mbti_router, prefix="/mbti", tags=["MBTI"])
app.include_router(ocean_router, prefix="/ocean", tags=["OCEAN"])