"""AI optimization API routes (Phase 5)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.response import success_response
from app.database import get_db
from app.models.user import User
from app.schemas.ai import (
    EnhanceRequest,
    EvaluateBatchRequest,
    EvaluateRequest,
    GenerateRequest,
    LintRequest,
    VariantRequest,
)
from app.services import ai_service

router = APIRouter()


@router.post("/generate")
async def generate(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await ai_service.generate_prompts(db, request, user_id=current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/enhance")
async def enhance(
    request: EnhanceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await ai_service.enhance_prompt(db, request, user_id=current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/variants")
async def variants(
    request: VariantRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await ai_service.generate_variants(db, request, user_id=current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/evaluate")
async def evaluate(
    request: EvaluateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await ai_service.evaluate_prompt(db, request, user_id=current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/evaluate/batch")
async def evaluate_batch(
    request: EvaluateBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await ai_service.evaluate_batch(db, request, user_id=current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/lint")
async def lint(
    request: LintRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await ai_service.lint_prompt(db, request, user_id=current_user.id)
    return success_response(data=result.model_dump(mode="json"))
