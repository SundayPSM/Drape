from fastapi import APIRouter
from app.api.v1 import auth, users, products, tryon

router = APIRouter()

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(products.router)
router.include_router(tryon.router)
