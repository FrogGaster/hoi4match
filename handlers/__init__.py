from aiogram import Router
from .start import router as start_router
from .profile import router as profile_router
from .search import router as search_router
from .stats import router as stats_router
from .admin import router as admin_router

def setup_routers() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(profile_router)
    router.include_router(search_router)
    router.include_router(stats_router)
    router.include_router(admin_router)
    return router
