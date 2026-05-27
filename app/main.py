from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import re

from app.auth.router import router as auth_router
from app.middleware.AuthMiddleware import AuthMiddleware
from app.product.router import router as product_router
from app.contact.router import router as contact_router
from app.product_category.router import router as product_category_router
from app.unit.router import router as unit
from app.order.router import router as orders
from app.config import client, env, fastapi_config
from app.petty_cash.router import router as petty_cash
from app.contact.utils import UPLOAD_DIR




def sanitize_filename(filename: str) -> str:
    """Sanitize filename by replacing invalid characters with underscores."""
    invalid_chars = r'[/\\:*?"<>|]'
    return re.sub(invalid_chars, '_', filename)

app = FastAPI(**fastapi_config)


@app.on_event("startup")
def startup_db_client():
    app.state.mongodb = client


@app.on_event("shutdown")
def shutdown_db_client():
    client.close()



# Add Auth middleware first so it runs earlier in the stack.
app.add_middleware(AuthMiddleware)

# Add CORS middleware after AuthMiddleware so CORS headers are always
# applied to responses (including ones returned by AuthMiddleware).
app.add_middleware(
    CORSMiddleware,
    allow_origins=env.cors_origins,
    allow_methods=env.cors_methods,
    allow_headers=env.cors_headers,
    allow_credentials=True,
)

# Mount static files after middleware so responses go through middleware stack
app.mount("/public", StaticFiles(directory=UPLOAD_DIR), name="public")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(product_router, prefix="/products", tags=["Product"])
app.include_router(contact_router, prefix="/contacts", tags=["Contact"])
app.include_router(
    product_category_router, prefix="/product-category", tags=["Product_Category"]
)
app.include_router(unit, prefix="/unit", tags=["Unit"])
app.include_router(orders, prefix="/orders", tags=["Orders"])
app.include_router(petty_cash, prefix="/petty-cash", tags=["Petty Cash"])


@app.get("/")
def root():
    return f"Documentation is available at {app.docs_url}"


@app.get("/download-static/contact/{file_name}")
def download_contact_file(file_name: str):
    """Serve a file from app/public/contact safely.

    Example: GET /download-static/contact/image_123.png
    """
    # Sanitize the filename
    file_name = sanitize_filename(file_name)
    
    # Additional path traversal validation
    if ".." in file_name or file_name.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file name"
        )

    base_dir = os.path.join(UPLOAD_DIR, "contact")
    file_path = os.path.join(base_dir, file_name)

    # Ensure resolved path is inside the base_dir
    try:
        if os.path.commonpath([os.path.abspath(file_path), os.path.abspath(base_dir)]) != os.path.abspath(base_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path"
            )
    except ValueError:
        # commonpath can raise ValueError on different drives on Windows
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path")

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(path=file_path, filename=file_name)
