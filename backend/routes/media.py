from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import os
import uuid
from pathlib import Path

from database import get_db
from dependencies import get_current_admin_user
from models import User, MediaAsset, MediaType

router = APIRouter(prefix="/api/admin/media", tags=["media"])
public_router = APIRouter(prefix="/api/public/media", tags=["public-media"])

# Configuração de uploads
UPLOAD_BASE_DIR = Path("uploads")
UPLOAD_DIRS = {
    MediaType.LOGO: UPLOAD_BASE_DIR / "logos",
    MediaType.BANNER: UPLOAD_BASE_DIR / "banners",
}

# Criar diretórios se não existirem
for upload_dir in UPLOAD_DIRS.values():
    upload_dir.mkdir(parents=True, exist_ok=True)

# Tipos de arquivo permitidos
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/svg+xml",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
RECOMMENDED_SIZE = 500 * 1024  # 500KB


def generate_filename(original_filename: str) -> str:
    """Gera nome único para arquivo"""
    ext = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(datetime.utcnow().timestamp())
    return f"{timestamp}-{unique_id}{ext}"


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    media_type: str = Form(...),  # "logo" ou "banner"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Upload de imagem (logo ou banner)"""
    try:
        # Validar tipo
        try:
            media_type_enum = MediaType(media_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo inválido. Use 'logo' ou 'banner'"
            )

        # Validar MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de arquivo não permitido. Use JPG, PNG, WebP ou SVG"
            )

        # Validar tamanho
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande (máximo 5MB, recomendado < 500KB)"
            )

        # Gerar nome único
        filename = generate_filename(file.filename)
        upload_dir = UPLOAD_DIRS[media_type_enum]
        file_path = upload_dir / filename

        # Salvar arquivo
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Verificar se arquivo foi salvo
        if not file_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Erro ao salvar arquivo"
            )

        # Obter próxima posição para banners
        position = 0
        if media_type_enum == MediaType.BANNER:
            max_position = db.query(func.max(MediaAsset.position)).filter(
                MediaAsset.type == MediaType.BANNER
            ).scalar()
            position = (max_position or 0) + 1

        # Determinar nome do diretório na URL (sempre plural: logos, banners)
        url_dir = "logos" if media_type_enum == MediaType.LOGO else "banners"
        
        # Salvar referência no banco (URL relativa que será servida pela rota /api/public/media/uploads/...)
        media_asset = MediaAsset(
            type=media_type_enum,
            url=f"/api/public/media/uploads/{url_dir}/{filename}",
            filename=filename,
            file_size=file_size,
            mime_type=file.content_type,
            is_active=True,
            position=position,
        )
        db.add(media_asset)
        db.commit()
        db.refresh(media_asset)

        return {
            "success": True,
            "id": media_asset.id,
            "url": media_asset.url,
            "filename": media_asset.filename,
            "type": media_asset.type.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao fazer upload: {str(e)}"
        )


@router.get("/list")
async def list_media(
    media_type: Optional[str] = None,  # "logo" ou "banner" ou None para todos
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar mídias (admin)"""
    query = db.query(MediaAsset)
    
    if media_type:
        try:
            media_type_enum = MediaType(media_type.lower())
            query = query.filter(MediaAsset.type == media_type_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo inválido. Use 'logo' ou 'banner'"
            )

    assets = query.order_by(MediaAsset.position.asc(), MediaAsset.created_at.desc()).all()
    
    return [
        {
            "id": asset.id,
            "type": asset.type.value,
            "url": asset.url,
            "filename": asset.filename,
            "file_size": asset.file_size,
            "mime_type": asset.mime_type,
            "is_active": asset.is_active,
            "position": asset.position,
            "created_at": asset.created_at.isoformat(),
        }
        for asset in assets
    ]


@router.delete("/{media_id}")
async def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deletar mídia"""
    asset = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Mídia não encontrada")

    # Deletar arquivo físico
    # Extrair path da URL: /api/public/media/uploads/logos/file.jpg -> logos/file.jpg
    url_path = asset.url.replace("/api/public/media/uploads/", "").lstrip("/")
    
    # Se ainda tiver prefixo, remover (compatibilidade com URLs antigas)
    if "/" in url_path:
        parts = url_path.split("/", 1)
        file_path = UPLOAD_BASE_DIR / parts[0] / parts[1] if len(parts) == 2 else UPLOAD_BASE_DIR / url_path
    else:
        # Fallback: usar diretório baseado no tipo
        upload_dir = UPLOAD_DIRS.get(asset.type)
        file_path = upload_dir / asset.filename if upload_dir else None
    
    if file_path and file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            print(f"Erro ao deletar arquivo físico: {e}")

    # Deletar do banco
    db.delete(asset)
    db.commit()

    return {"success": True, "message": "Mídia deletada com sucesso"}


@router.put("/{media_id}/position")
async def update_position(
    media_id: int,
    position: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualizar posição de banner"""
    asset = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Mídia não encontrada")

    asset.position = position
    db.commit()
    db.refresh(asset)

    return {
        "success": True,
        "id": asset.id,
        "position": asset.position,
    }


@router.put("/{media_id}/toggle-active")
async def toggle_active(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Ativar/desativar mídia"""
    asset = db.query(MediaAsset).filter(MediaAsset.id == media_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Mídia não encontrada")

    asset.is_active = not asset.is_active
    db.commit()
    db.refresh(asset)

    return {
        "success": True,
        "id": asset.id,
        "is_active": asset.is_active,
    }


# ========== ROTAS PÚBLICAS ==========

@public_router.get("/banners")
async def get_public_banners(db: Session = Depends(get_db)):
    """Listar banners ativos (público)"""
    banners = db.query(MediaAsset).filter(
        MediaAsset.type == MediaType.BANNER,
        MediaAsset.is_active == True
    ).order_by(MediaAsset.position.asc()).all()

    return [
        {
            "id": banner.id,
            "url": banner.url,
            "position": banner.position,
        }
        for banner in banners
    ]


@public_router.get("/logo")
async def get_public_logo(db: Session = Depends(get_db)):
    """Obter logo ativa (público)"""
    logo = db.query(MediaAsset).filter(
        MediaAsset.type == MediaType.LOGO,
        MediaAsset.is_active == True
    ).order_by(MediaAsset.created_at.desc()).first()

    if not logo:
        return {"url": None}

    return {"url": logo.url}


# Servir arquivos estáticos
@public_router.get("/uploads/{media_type}/{filename}")
async def serve_uploaded_file(media_type: str, filename: str):
    """Servir arquivo de upload"""
    # Mapear tipo da URL para diretório físico (plural)
    dir_mapping = {
        "logo": "logos",
        "logos": "logos",
        "banner": "banners",
        "banners": "banners",
        "promotion": "promotions",
        "promotions": "promotions",
    }
    upload_dir = dir_mapping.get(media_type.lower(), media_type)
    file_path = UPLOAD_BASE_DIR / upload_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {file_path}")

    return FileResponse(
        file_path,
        media_type="image/jpeg"  # FastAPI vai detectar automaticamente
    )
