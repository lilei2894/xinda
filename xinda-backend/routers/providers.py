from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db, Provider, ModelEntry
import os
import httpx

router = APIRouter()


@router.get("")
async def list_providers(db: Session = Depends(get_db)):
    providers = db.query(Provider).all()
    result = []
    for p in providers:
        result.append({
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "base_url": p.base_url,
            "api_key": "***" if p.api_key else None,
            "is_active": p.is_active,
            "models": [
                {
                    "id": m.id,
                    "model_id": m.model_id,
                    "display_name": m.display_name,
                    "model_type": m.model_type,
                    "is_default": m.is_default,
                    "is_active": m.is_active,
                }
                for m in p.models
            ]
        })
    return result


@router.post("", status_code=201)
async def create_provider(data: dict, db: Session = Depends(get_db)):
    existing = db.query(Provider).filter(Provider.name == data.get("name")).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider name already exists")
    
    provider = Provider(
        name=data["name"],
        display_name=data.get("display_name", data["name"]),
        base_url=data["base_url"],
        api_key=data.get("api_key"),
        is_active="true",
    )
    db.add(provider)
    db.flush()
    
    models = data.get("models", [])
    for m in models:
        model_id = m.get("id", "").strip()
        display_name = m.get("name", "").strip()
        if model_id and display_name:
            model = ModelEntry(
                provider_id=provider.id,
                model_id=model_id,
                display_name=display_name,
                model_type="both",
                is_default="false",
            )
            db.add(model)
    
    db.commit()
    db.refresh(provider)
    
    return {
        "id": provider.id,
        "name": provider.name,
        "display_name": provider.display_name,
        "base_url": provider.base_url,
        "api_key": "***" if provider.api_key else None,
        "is_active": provider.is_active,
        "models": [
            {
                "id": m.id,
                "model_id": m.model_id,
                "display_name": m.display_name,
                "model_type": m.model_type,
                "is_default": m.is_default,
            }
            for m in provider.models
        ]
    }


@router.put("/{provider_id}")
async def update_provider(provider_id: int, data: dict, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    if "display_name" in data:
        provider.display_name = data["display_name"]
    if "base_url" in data:
        provider.base_url = data["base_url"]
    if "api_key" in data:
        provider.api_key = data["api_key"]
    if "is_active" in data:
        provider.is_active = data["is_active"]
    if "name" in data:
        provider.name = data["name"]
    
    db.commit()
    db.refresh(provider)
    return {"id": provider.id, "name": provider.name, "display_name": provider.display_name, "base_url": provider.base_url}


@router.delete("/{provider_id}")
async def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    db.delete(provider)
    db.commit()
    return {"message": "Provider deleted"}


@router.get("/{provider_id}/models")
async def get_provider_models(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    models = [
        {
            "id": m.id,
            "model_id": m.model_id,
            "display_name": m.display_name,
            "model_type": m.model_type,
            "is_default": m.is_default,
        }
        for m in provider.models
    ]
    
    if provider.name == "ollama":
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{provider.base_url}/api/tags")
                if resp.status_code == 200:
                    ollama_models = resp.json().get("models", [])
                    existing_ids = {m["model_id"] for m in models}
                    for om in ollama_models:
                        mid = om.get("name", "")
                        if mid and mid not in existing_ids:
                            models.append({
                                "id": None,
                                "model_id": mid,
                                "display_name": mid,
                                "model_type": "both",
                                "is_default": "false",
                            })
        except Exception:
            pass
    
    return models


@router.post("/fetch-models")
async def fetch_models(data: dict):
    base_url = data.get("base_url", "").rstrip('/')
    api_key = data.get("api_key")
    provider_name = data.get("name", "")
    
    models = []
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    if provider_name == "ollama":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{base_url}/api/tags")
                if resp.status_code == 200:
                    ollama_models = resp.json().get("models", [])
                    for om in ollama_models:
                        mid = om.get("name", "")
                        if mid:
                            models.append({
                                "model_id": mid,
                                "display_name": mid,
                                "model_type": "both",
                                "is_default": "false",
                                "is_active": "true",
                            })
        except Exception:
            pass
    else:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                models_url = f"{base_url}/models" if base_url.endswith('/v1') else f"{base_url}/v1/models"
                resp = await client.get(models_url, headers=headers)
                if resp.status_code == 200:
                    api_models = resp.json().get("data", [])
                    for am in api_models:
                        mid = am.get("id", "")
                        if mid:
                            models.append({
                                "model_id": mid,
                                "display_name": mid,
                                "model_type": "both",
                                "is_default": "false",
                                "is_active": "true",
                            })
        except Exception:
            pass
            
    return {"models": models}


@router.post("/{provider_id}/test")
async def test_provider_connection(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider.name == "ollama":
                resp = await client.get(f"{provider.base_url}/api/tags")
                if resp.status_code == 200:
                    return {"status": "connected", "message": f"Connected to {provider.display_name}"}
                else:
                    return {"status": "error", "message": f"Unexpected response: {resp.status_code}"}
            else:
                resp = await client.get(provider.base_url)
                if resp.status_code in (200, 401, 403, 404):
                    return {"status": "connected", "message": f"Server reachable: {provider.display_name}"}
                else:
                    return {"status": "error", "message": f"Unexpected response: {resp.status_code}"}
    except httpx.ConnectError:
        return {"status": "error", "message": f"Cannot connect to {provider.base_url}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.put("/{provider_id}/models")
async def update_provider_models(provider_id: int, data: dict, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    if "display_name" in data:
        provider.display_name = data["display_name"]
    if "base_url" in data:
        provider.base_url = data["base_url"]
    if "api_key" in data and data["api_key"] and data["api_key"] != "***":
        provider.api_key = data["api_key"]
    if "is_active" in data:
        provider.is_active = data["is_active"]
    if "name" in data:
        provider.name = data["name"]
    
    if "models" in data:
        db.query(ModelEntry).filter(ModelEntry.provider_id == provider_id).delete()
        for m in data["models"]:
            model_id = m.get("model_id", "").strip()
            display_name = m.get("display_name", "").strip()
            if model_id and display_name:
                model = ModelEntry(
                    provider_id=provider.id,
                    model_id=model_id,
                    display_name=display_name,
                    model_type=m.get("model_type", "both"),
                    is_default=m.get("is_default", "false"),
                    is_active=m.get("is_active", "true"),
                )
                db.add(model)
    
    db.commit()
    db.refresh(provider)
    
    return {
        "id": provider.id,
        "name": provider.name,
        "display_name": provider.display_name,
        "base_url": provider.base_url,
        "api_key": "***" if provider.api_key else None,
        "is_active": provider.is_active,
        "models": [
            {
                "id": m.id,
                "model_id": m.model_id,
                "display_name": m.display_name,
                "model_type": m.model_type,
                "is_default": m.is_default,
                "is_active": m.is_active,
            }
            for m in provider.models
        ]
    }


@router.patch("/models/{model_id}/toggle")
async def toggle_model(model_id: int, data: dict, db: Session = Depends(get_db)):
    model = db.query(ModelEntry).filter(ModelEntry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model.is_active = data.get("is_active", "true")
    db.commit()
    db.refresh(model)
    
    return {
        "id": model.id,
        "model_id": model.model_id,
        "display_name": model.display_name,
        "is_active": model.is_active,
    }
