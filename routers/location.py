from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from ..services.location_service import LocationService
from ..schemas.location import *

router = APIRouter(prefix="/api/v1/locations",
                    tags=["locations"])
 

def get_location_service() -> LocationService:
    return LocationService()

@router.get("/counties/", response_model=List[CountySimple])
async def get_counties(service: LocationService = Depends(get_location_service)):
    """Get list of all counties"""
    return service.get_all_counties()

@router.get("/counties/{county_identifier}/", response_model=dict)
async def get_county_constituencies(
    county_identifier: str,
    service: LocationService = Depends(get_location_service)
):
    """Get constituencies for a specific county use ID or name"""
    return service.get_constituencies(county_identifier)

@router.get("/counties/{county_identifier}/constituencies/{constituency_name}/", response_model=WardResponse)
async def get_constituency_wards(
    county_identifier: str,
    constituency_name: str,
    service: LocationService = Depends(get_location_service)
):
    """Get wards for a specific constituency"""
    return service.get_wards(county_identifier, constituency_name)

@router.get("/counties/{county_identifier}/tree/", response_model=County)
async def get_county_tree(
    county_identifier: str,
    service: LocationService = Depends(get_location_service)
):
    """Get complete county hierarchy (constituencies and wards)"""
    return service.get_county_tree(county_identifier)

@router.get("/search/", response_model=SearchResult)
async def search_locations(
    q: str = Query(..., min_length=2, description="Search query"),
    service: LocationService = Depends(get_location_service)
):
    """Search across counties, constituencies, and wards"""
    return service.search_locations(q)

@router.get("/coordinates/reverse/", response_model=LocationDetails)
async def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    service: LocationService = Depends(get_location_service)
):
    """Get location details from coordinates"""
    if not (-90 <= lat <= 90):
        raise HTTPException(status_code=400, detail="Invalid latitude")
    if not (-180 <= lng <= 180):
        raise HTTPException(status_code=400, detail="Invalid longitude")
    
    return await service.reverse_geocode(lat, lng)

@router.get("/search/geocode/", response_model=List[LocationDetails])
async def forward_geocode(
    address: str = Query(..., min_length=3, description="Address or place name"),
    service: LocationService = Depends(get_location_service)
):
    """Get coordinates from address/place name"""
    return await service.forward_geocode(address)