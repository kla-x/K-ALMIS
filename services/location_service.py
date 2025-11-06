import json
import os
from typing import List, Optional
from fastapi import HTTPException
import requests
from ..schemas.location import *

class LocationService:
    def __init__(self):
        self.counties_data = self._load_counties_data()
    
    def _load_counties_data(self) -> List[County]:
        fpath = os.path.join(os.path.dirname(__file__),"counties.json")
       
        try:
            with open(fpath, "r", encoding="utf-8") as file:
                data = json.load(file)
                return [County(**county) for county in data]
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Counties data file not found")
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Counties Datafile invalid")
    
    def get_all_counties(self) -> List[CountySimple]:
        return [
            CountySimple(county_code=county.county_code, county_name=county.county_name)
            for county in self.counties_data
        ]
    
    def get_county_by_id_or_name(self, identifier: str) -> Optional[County]:
        try:
            county_id = int(identifier)
            for county in self.counties_data:
                if county.county_code == county_id:
                    return county
        except ValueError: #not int
            identifier_lower = identifier.lower().strip()
            for county in self.counties_data:
                if county.county_name.lower() == identifier_lower:
                    return county
        return None
    
    def get_constituencies(self, county_identifier: str) -> Dict:
        county = self.get_county_by_id_or_name(county_identifier)
        if not county:
            raise HTTPException(status_code=404, detail="County not found")
        
        return {
            "county_code": county.county_code,
            "county_name": county.county_name,
            "constituencies": [
                ConstituencySimple(constituency_name=const.constituency_name)
                for const in county.constituencies
            ]
        }
    
    def get_wards(self, county_identifier: str, constituency_name: str) -> WardResponse:
        county = self.get_county_by_id_or_name(county_identifier)
        if not county:
            raise HTTPException(status_code=404, detail="County not found")
        
        constituency_lower = constituency_name.lower().strip()
        for const in county.constituencies:
            if const.constituency_name.lower() == constituency_lower:
                return WardResponse(
                    county_name=county.county_name,
                    constituency_name=const.constituency_name,
                    wards=const.wards
                )
        
        raise HTTPException(status_code=404, detail="Constituency not found")
    
    def get_county_tree(self, county_identifier: str) -> County:
        county = self.get_county_by_id_or_name(county_identifier)
        if not county:
            raise HTTPException(status_code=404, detail="County not found")
        return county
    
    def search_locations(self, query: str) -> SearchResult:
        if not query or len(query.strip()) < 2:
            return SearchResult()
        
        query_lower = query.lower().strip()
        result = SearchResult()
        
        for county in self.counties_data:
            # counties
            if query_lower in county.county_name.lower():
                result.counties.append(
                    CountySimple(county_code=county.county_code, county_name=county.county_name)
                )
            # situency
            for const in county.constituencies:
                if query_lower in const.constituency_name.lower():
                    result.constituencies.append({
                        "constituency_name": const.constituency_name,
                        "county_name": county.county_name,
                        "county_code": county.county_code
                    })
                
                # ma word
                for ward in const.wards:
                    if query_lower in ward.lower():
                        result.wards.append({
                            "ward_name": ward,
                            "constituency_name": const.constituency_name,
                            "county_name": county.county_name,
                            "county_code": county.county_code
                        })
        
        return result
    
    async def reverse_geocode(self, lat: float, lng: float) -> LocationDetails:
        try:
            url = f"https://nominatim.openstreetmap.org/reverse"
            params = {
                "format": "json",
                "lat": lat,
                "lon": lng,
                "addressdetails": 1,
                "accept-language": "en"
            }
            headers = {"User-Agent": "AssetManagementApp/v1.0"}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
     
            address = data.get("display_name", "")
            
            administrative = self._match_administrative_location(data.get("address", {}))
            
            return LocationDetails(
                coordinates=Coordinates(lat=lat, lng=lng),
                address=address,
                administrative=administrative
            )
            
        except requests.RequestException:
            return LocationDetails(
                coordinates=Coordinates(lat=lat, lng=lng),
                administrative=AdministrativeLocation()
            )
    
    async def forward_geocode(self, address: str) -> List[LocationDetails]:
        """Get coordinates from address/place name"""
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "format": "json",
                "q": f"{address}, Kenya",
                "limit": 5,
                "addressdetails": 1,
                "accept-language": "en"
            }
            headers = {"User-Agent": "AssetManagementApp/1.0"}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data:
                lat = float(item.get("lat", 0))
                lng = float(item.get("lon", 0))
                
                administrative = self._match_administrative_location(item.get("address", {}))
                
                results.append(LocationDetails(
                    coordinates=Coordinates(lat=lat, lng=lng),
                    address=item.get("display_name", ""),
                    administrative=administrative
                ))
            
            return results
            
        except requests.RequestException:
            raise HTTPException(status_code=503, detail="Geocoding service unavailable")
    
    def _match_administrative_location(self, address_data: dict) -> AdministrativeLocation:
        """Try to match OSM address data with Kenya administrative boundaries"""
        # Extract potential county/region names from OSM data
        potential_county = (
            address_data.get("county") or 
            address_data.get("state") or 
            address_data.get("region") or ""
        ).strip()
        
        matched_county = None
        matched_constituency = None
        matched_ward = None
        
        if potential_county:
            for county in self.counties_data:
                if county.county_name.lower() in potential_county.lower() or potential_county.lower() in county.county_name.lower():
                    matched_county = county.county_name
                    break
        
        if matched_county:
            county = next((c for c in self.counties_data if c.county_name == matched_county), None)
            if county: # try to match other compontents
                location_components = [
                    address_data.get("suburb", ""),
                    address_data.get("village", ""),
                    address_data.get("town", ""),
                    address_data.get("city_district", ""),
                    address_data.get("neighbourhood", "")
                ]
                
                for component in location_components:
                    if not component:
                        continue
                    
                    component_lower = component.lower()
                    
                    for const in county.constituencies:
                        if const.constituency_name.lower() in component_lower or component_lower in const.constituency_name.lower():
                            matched_constituency = const.constituency_name
                            
                           
                            for ward in const.wards: # Try to match ward within curr constituency
                                if ward.lower() in component_lower or component_lower in ward.lower():
                                    matched_ward = ward
                                    break
                            break
                    
                    if matched_constituency:
                        break
        
        return AdministrativeLocation(
            county=matched_county,
            constituency=matched_constituency,
            ward=matched_ward)