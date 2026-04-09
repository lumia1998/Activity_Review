import base64
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from PIL import Image

from ..core.paths import resolve_data_dir

router = APIRouter()


def resolve_screenshot_path(relative_path: str) -> Path:
    normalized = Path(relative_path.replace('\\', '/'))
    candidate = resolve_data_dir() / normalized
    try:
        candidate.resolve().relative_to(resolve_data_dir().resolve())
    except ValueError as error:
        raise HTTPException(status_code=400, detail='invalid screenshot path') from error
    return candidate


def encode_image_base64(image_path: Path, max_width: int | None = None) -> str:
    if not image_path.exists() or not image_path.is_file():
        raise HTTPException(status_code=404, detail='screenshot not found')

    with Image.open(image_path) as image:
        image = image.convert('RGB')
        if max_width and image.width > max_width:
            ratio = max_width / image.width
            image = image.resize((max_width, max(1, int(image.height * ratio))), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=85, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode('ascii')


@router.get('/thumbnail')
async def screenshot_thumbnail(path: str = Query(...)) -> str:
    return encode_image_base64(resolve_screenshot_path(path), max_width=400)


@router.get('/full')
async def screenshot_full(path: str = Query(...)) -> str:
    return encode_image_base64(resolve_screenshot_path(path), max_width=1200)
