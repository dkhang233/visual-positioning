from fastapi import FastAPI
from routes.localize import localize_router  # import router từ file/module bạn đã tạo

app = FastAPI()
app.include_router(localize_router)
