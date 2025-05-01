from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class LocalizaionFailed(Exception):
    def __init__(self, message: str = "Localization failed"):
        self.message = message
        super().__init__(self.message)



async def http_exception_handler(request: Request, exc: LocalizaionFailed):
    return JSONResponse(
        status_code=400,
        content={"message": exc.message}
    )