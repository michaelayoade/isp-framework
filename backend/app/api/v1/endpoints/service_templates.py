"""
Service Templates API Endpoints - ISP Service Management System

REST API endpoints for managing service templates including:
- Base service templates (CRUD, search, statistics)
- Internet service templates (specialized configuration)
- Voice service templates (calling features)
- Bundle service templates (multi-service packages)

Provides comprehensive template management for ISP service offerings.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.auth import Administrator
from app.models.services.enums import ServiceType
from app.schemas.service_management import (  # Service Template Schemas; Internet Service Template Schemas; Voice Service Template Schemas
    BundleServiceTemplate,
    BundleServiceTemplateCreate,
    InternetServiceTemplate,
    InternetServiceTemplateCreate,
    InternetServiceTemplateUpdate,
    ServiceTemplate,
    ServiceTemplateCreate,
    ServiceTemplateListResponse,
    ServiceTemplateUpdate,
    VoiceServiceTemplate,
    VoiceServiceTemplateCreate,
)
from app.services.service_layer_factory import get_service_layer_factory

from ..dependencies import get_current_admin

router = APIRouter()


# ============================================================================
# Base Service Template Endpoints
# ============================================================================


@router.post("/", response_model=ServiceTemplate, status_code=status.HTTP_201_CREATED)
async def create_service_template(
    template_data: ServiceTemplateCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Create a new service template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    try:
        template = await template_service.create_template(
            template_data=template_data.dict(), admin_id=current_admin.id
        )
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create template: {str(e)}"
        )


@router.get("/", response_model=ServiceTemplateListResponse)
async def list_service_templates(
    service_type: Optional[ServiceType] = Query(
        None, description="Filter by service type"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_public: Optional[bool] = Query(None, description="Filter by public visibility"),
    location_id: Optional[int] = Query(None, description="Filter by location"),
    search_query: Optional[str] = Query(
        None, description="Search in name and description"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """List service templates with filtering and pagination"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    # Build filters
    filters = {}
    if service_type:
        filters["service_type"] = service_type
    if is_active is not None:
        filters["is_active"] = is_active
    if is_public is not None:
        filters["is_public"] = is_public
    if location_id:
        filters["location_id"] = location_id
    if search_query:
        filters["search_query"] = search_query

    try:
        templates, total = await template_service.search_templates(
            filters=filters, page=page, size=size
        )

        return ServiceTemplateListResponse(
            items=templates,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size if total > 0 else 0,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/{template_id}", response_model=ServiceTemplate)
async def get_service_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get a specific service template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    try:
        template = await template_service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@router.put("/{template_id}", response_model=ServiceTemplate)
async def update_service_template(
    template_id: int,
    template_data: ServiceTemplateUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Update a service template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    try:
        template = await template_service.update_template(
            template_id=template_id,
            update_data=template_data.dict(exclude_unset=True),
            admin_id=current_admin.id,
        )
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Delete (deactivate) a service template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    try:
        success = await template_service.deactivate_template(
            template_id=template_id, admin_id=current_admin.id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete template: {str(e)}"
        )


@router.post("/{template_id}/activate", response_model=ServiceTemplate)
async def activate_service_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Activate a service template"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    try:
        template = await template_service.activate_template(
            template_id=template_id, admin_id=current_admin.id
        )
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to activate template: {str(e)}"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_template_statistics(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get service template statistics"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    try:
        stats = await template_service.get_template_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


# ============================================================================
# Internet Service Template Endpoints
# ============================================================================


@router.post(
    "/internet",
    response_model=InternetServiceTemplate,
    status_code=status.HTTP_201_CREATED,
)
async def create_internet_service_template(
    template_data: InternetServiceTemplateCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Create a new internet service template"""
    factory = get_service_layer_factory(db)
    internet_service = factory.get_internet_template_service()

    try:
        template = await internet_service.create_internet_template(
            template_data=template_data.dict(), admin_id=current_admin.id
        )
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create internet template: {str(e)}"
        )


@router.get("/internet", response_model=List[InternetServiceTemplate])
async def list_internet_service_templates(
    min_download_speed: Optional[int] = Query(
        None, description="Minimum download speed in kbps"
    ),
    max_download_speed: Optional[int] = Query(
        None, description="Maximum download speed in kbps"
    ),
    has_data_limit: Optional[bool] = Query(
        None, description="Filter by data limit presence"
    ),
    static_ip_included: Optional[bool] = Query(
        None, description="Filter by static IP inclusion"
    ),
    router_included: Optional[bool] = Query(
        None, description="Filter by router inclusion"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """List internet service templates with filtering"""
    factory = get_service_layer_factory(db)
    internet_service = factory.get_internet_template_service()

    # Build filters
    filters = {}
    if min_download_speed:
        filters["min_download_speed"] = min_download_speed
    if max_download_speed:
        filters["max_download_speed"] = max_download_speed
    if has_data_limit is not None:
        filters["has_data_limit"] = has_data_limit
    if static_ip_included is not None:
        filters["static_ip_included"] = static_ip_included
    if router_included is not None:
        filters["router_included"] = router_included

    try:
        templates, _ = await internet_service.search_internet_templates(
            filters=filters, page=page, size=size
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list internet templates: {str(e)}"
        )


@router.get("/internet/{template_id}", response_model=InternetServiceTemplate)
async def get_internet_service_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get a specific internet service template"""
    factory = get_service_layer_factory(db)
    internet_service = factory.get_internet_template_service()

    try:
        template = await internet_service.get_internet_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Internet template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get internet template: {str(e)}"
        )


@router.put("/internet/{template_id}", response_model=InternetServiceTemplate)
async def update_internet_service_template(
    template_id: int,
    template_data: InternetServiceTemplateUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Update an internet service template"""
    factory = get_service_layer_factory(db)
    internet_service = factory.get_internet_template_service()

    try:
        template = await internet_service.update_internet_template(
            template_id=template_id,
            update_data=template_data.dict(exclude_unset=True),
            admin_id=current_admin.id,
        )
        if not template:
            raise HTTPException(status_code=404, detail="Internet template not found")
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update internet template: {str(e)}"
        )


# ============================================================================
# Voice Service Template Endpoints
# ============================================================================


@router.post(
    "/voice", response_model=VoiceServiceTemplate, status_code=status.HTTP_201_CREATED
)
async def create_voice_service_template(
    template_data: VoiceServiceTemplateCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Create a new voice service template"""
    factory = get_service_layer_factory(db)
    voice_service = factory.get_voice_template_service()

    try:
        template = await voice_service.create_voice_template(
            template_data=template_data.dict(), admin_id=current_admin.id
        )
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create voice template: {str(e)}"
        )


@router.get("/voice", response_model=List[VoiceServiceTemplate])
async def list_voice_service_templates(
    is_unlimited: Optional[bool] = Query(
        None, description="Filter by unlimited minutes"
    ),
    international_calling: Optional[bool] = Query(
        None, description="Filter by international calling"
    ),
    voicemail: Optional[bool] = Query(None, description="Filter by voicemail feature"),
    conference_calling: Optional[bool] = Query(
        None, description="Filter by conference calling"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """List voice service templates with filtering"""
    factory = get_service_layer_factory(db)
    voice_service = factory.get_voice_template_service()

    # Build filters
    filters = {}
    if is_unlimited is not None:
        filters["is_unlimited"] = is_unlimited
    if international_calling is not None:
        filters["international_calling"] = international_calling
    if voicemail is not None:
        filters["voicemail"] = voicemail
    if conference_calling is not None:
        filters["conference_calling"] = conference_calling

    try:
        templates, _ = await voice_service.search_voice_templates(
            filters=filters, page=page, size=size
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list voice templates: {str(e)}"
        )


@router.get("/voice/{template_id}", response_model=VoiceServiceTemplate)
async def get_voice_service_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get a specific voice service template"""
    factory = get_service_layer_factory(db)
    voice_service = factory.get_voice_template_service()

    try:
        template = await voice_service.get_voice_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Voice template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get voice template: {str(e)}"
        )


# ============================================================================
# Bundle Service Template Endpoints
# ============================================================================


@router.post(
    "/bundle", response_model=BundleServiceTemplate, status_code=status.HTTP_201_CREATED
)
async def create_bundle_service_template(
    template_data: BundleServiceTemplateCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Create a new bundle service template"""
    factory = get_service_layer_factory(db)
    bundle_service = factory.get_bundle_template_service()

    try:
        template = await bundle_service.create_bundle_template(
            template_data=template_data.dict(), admin_id=current_admin.id
        )
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create bundle template: {str(e)}"
        )


@router.get("/bundle", response_model=List[BundleServiceTemplate])
async def list_bundle_service_templates(
    service_types: Optional[List[ServiceType]] = Query(
        None, description="Filter by included service types"
    ),
    min_discount: Optional[float] = Query(
        None, description="Minimum discount percentage"
    ),
    has_contract: Optional[bool] = Query(
        None, description="Filter by contract requirement"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """List bundle service templates with filtering"""
    factory = get_service_layer_factory(db)
    bundle_service = factory.get_bundle_template_service()

    # Build filters
    filters = {}
    if service_types:
        filters["service_types"] = service_types
    if min_discount:
        filters["min_discount"] = min_discount
    if has_contract is not None:
        filters["has_contract"] = has_contract

    try:
        templates, _ = await bundle_service.search_bundle_templates(
            filters=filters, page=page, size=size
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list bundle templates: {str(e)}"
        )


@router.get("/bundle/{template_id}", response_model=BundleServiceTemplate)
async def get_bundle_service_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get a specific bundle service template"""
    factory = get_service_layer_factory(db)
    bundle_service = factory.get_bundle_template_service()

    try:
        template = await bundle_service.get_bundle_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Bundle template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get bundle template: {str(e)}"
        )


# ============================================================================
# Template Availability and Validation Endpoints
# ============================================================================


@router.get("/available", response_model=List[ServiceTemplate])
async def get_available_templates(
    location_id: Optional[int] = Query(
        None, description="Filter by location availability"
    ),
    service_type: Optional[ServiceType] = Query(
        None, description="Filter by service type"
    ),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Get available service templates for a location"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    try:
        templates = await template_service.get_available_templates(
            location_id=location_id, service_type=service_type
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get available templates: {str(e)}"
        )


@router.post("/{template_id}/validate", response_model=Dict[str, Any])
async def validate_template_for_customer(
    template_id: int,
    customer_id: int = Query(..., description="Customer ID to validate against"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Validate if a template can be assigned to a customer"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    try:
        validation_result = await template_service.validate_template_for_customer(
            template_id=template_id, customer_id=customer_id
        )
        return validation_result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to validate template: {str(e)}"
        )


# ============================================================================
# Template Import/Export Endpoints
# ============================================================================


@router.post("/import", response_model=Dict[str, Any])
async def import_templates(
    templates_data: List[ServiceTemplateCreate],
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Import multiple service templates"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    results = {"total": len(templates_data), "successful": 0, "failed": 0, "errors": []}

    for template_data in templates_data:
        try:
            await template_service.create_template(
                template_data=template_data.dict(), admin_id=current_admin.id
            )
            results["successful"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Template '{template_data.name}': {str(e)}")

    return results


@router.get("/export", response_model=List[ServiceTemplate])
async def export_templates(
    service_type: Optional[ServiceType] = Query(
        None, description="Filter by service type"
    ),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
):
    """Export service templates"""
    factory = get_service_layer_factory(db)
    template_service = factory.get_service_template_service()

    filters = {"is_active": is_active}
    if service_type:
        filters["service_type"] = service_type

    try:
        templates, _ = await template_service.search_templates(
            filters=filters, page=1, size=1000  # Large size for export
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export templates: {str(e)}"
        )
