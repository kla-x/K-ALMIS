from fastapi import APIRouter,Depends
from ..models import User,EntityType,GovLevel
from typing import Dict,List
from ..utilities import get_current_user

router = APIRouter(
    prefix="/api/v1/user/supp",
    tags=["GEneral Supporting routes"]
    )



@router.get("/entitytype",status_code=200,response_model=Dict[str, str])
async def list_entitiy_types(curr: User = Depends(get_current_user)):

    return {x.name: x.value for x in EntityType}


@router.get("/govlevel",status_code=200,response_model=Dict[str, str])
async def show_goverment_levels (curr: User = Depends(get_current_user)):

    return {x.name: x.value for x in GovLevel}
