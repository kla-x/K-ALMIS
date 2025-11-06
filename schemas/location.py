from pydantic import BaseModel, Field
from typing import List, Optional, Dict
 


class Ward(BaseModel):
    name: str

class Constituency(BaseModel):
    constituency_name: str
    wards: List[str]

class County(BaseModel):
    county_code: int
    county_name: str
    constituencies: List[Constituency]

class CountySimple(BaseModel):
    county_code: int
    county_name: str

class ConstituencySimple(BaseModel):
    constituency_name: str

class WardResponse(BaseModel):
    county_name: str
    constituency_name: str
    wards: List[str]

class Coordinates(BaseModel):
    lat: Optional[float] = Field(None, example=-0.7832) 
    lng: Optional[float] = Field(None, example=37.0400)


class AdministrativeLocation(BaseModel):
    county: Optional[str] = Field(None, example="Murang'a")
    constituency: Optional[str] = Field(None, example="Kandara")
    ward: Optional[str] = Field(None, example="Ithiru")

class LocationDetails(BaseModel):
    coordinates: Coordinates
    address: Optional[str] = Field(None, example="Kangari Market, Murang'a")
    administrative: AdministrativeLocation

class SearchResult(BaseModel):
    counties: List[CountySimple] = []
    constituencies: List[Dict[str, str]] = [] 
    wards: List[Dict[str, str]] = []


class LocationPreview(BaseModel):
    administrative_location: Optional[AdministrativeLocation] = None
    coordinates: Optional[Coordinates] = None
    address: Optional[str] = Field(None, example="Kangari Market, Murang'a")

    class Config:
        schema_extra = {
            "example": {
                "administrative_location": {
                    "county": "Murang'a",
                    "constituency": "Kandara",
                    "ward": "Ithiru"
                },
                "coordinates": {
                    "lat": -0.7832,
                    "lng": 37.0400
                },
                "address": "Kangari Market, Murang'a"
            }
        }