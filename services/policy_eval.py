from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session, Query
from fastapi import HTTPException
import logging
from ..models import ABACPolicy, User, Role, Assets
from ..system_vars import sys_logger,debugging
from ..services.logger_queue import enqueue_log
from ..schemas.main import  ActionType, LogLevel

logger = logging.getLogger(__name__)

def get_user_perms(db: Session, id: Optional[str] = None, user: Optional[User] = None):
    def get_u_p(user: User):
        role_perms = db.query(Role).filter(Role.id == user.role_id).first()
        
        if not role_perms:
            raise HTTPException(status_code=404, detail="Not Assigned role")

        rperm = role_perms.permissions or []
        aperm = user.assigned_perms or []
        perms = list(set(rperm) | set(aperm))
        perms = sorted(perms)
        return perms
    
    if user:
        return get_u_p(user)
    
    user = db.query(User).filter(User.id == id).first()
    return get_u_p(user)

def get_default_scope(user: User) -> Dict:
    default_scope = {
        "departments": [user.department_id],
        "geographic": [],
        "asset_categories": [],
        "value_limits": {}
    }
        #will expland for asset val and cat--future
    if user.location and isinstance(user.location, dict):
        admin_loc = user.location.get("administrative_location", {})
        if admin_loc.get("county"):
            county_name = admin_loc["county"].lower().replace(" ", "_")
            default_scope["geographic"] = [county_name]
    
    return default_scope

# def get_merged_scope(user: User) -> Dict:
#     default = get_default_scope(user)
    
#     if not user.access_scope:
#         return default
    
#     merged = default.copy()
#     for key, value in user.access_scope.items():
#         if key in merged:
#             merged[key] = value
    
#     return merged
import json
def get_merged_scope(user: User) -> dict:
    default = get_default_scope(user)
    if not user.access_scope:
        return default

    scope_data = user.access_scope
    if isinstance(scope_data, str):
        scope_data = json.loads(scope_data)  # convert JSON string → dict

    merged = default.copy()
    for key, value in scope_data.items():
        if key in merged:
            merged[key] = value
    return merged

def check_role_permission(user, action: str) -> Tuple[bool, str]:
    """1.check in (role + assigned) perms has the required perm

    Args:
        user (User): user obj
        action (str): fomat 'resource.action'

    Returns:
        Tuple[bool, str]: str for description
    """
    if not user.role:
        return False, "User has no role assigned" 
    
    r_perms = user.role.permissions or []
    assigned_perms = user.assigned_perms or []
    all_perms = list(set(r_perms) | set(assigned_perms))
    
    if action in all_perms:
        return True, "Permission granted by role or assigned permissions"
    if  "*.*" in r_perms:
        return True, "Permission granted by role or assigned permissions"
        
    
    return False, f"Action '{action}' not permitted"

def check_access_scope(user, resource: Optional[Dict] = None, action: str = None) -> Tuple[bool, str]:
    """ 2: Check user's access scope"""
    if not resource:
        return True, "No resource to check scope against"
    
    scope = get_merged_scope(user)

    if resource.get("department") and resource["department"] != user.department_id:
        allowed_deps = scope.get("departments", [])
        if allowed_deps and "*" not in allowed_deps:
            if resource["department"] not in allowed_deps:
                return False, f"Department access denied: {resource['department']}"
    # Geo
    if resource.get("county"):
        allowed_counties = scope.get("geographic", [])
        if allowed_counties:
            resource_county = resource["county"].lower().replace(" ", "_")
            if resource_county not in allowed_counties:
                return False, f"Geographic access denied for county: {resource['county']}"
    
    if resource.get("category"):
        allowed_categories = scope.get("asset_categories", [])
        if allowed_categories and "*" not in allowed_categories:
            if resource["category"] not in allowed_categories:
                return False, f"Asset category access denied: {resource['category']}"
    
    if resource.get("value"):
        value_limits = scope.get("value_limits", {})
        
        if action and "create" in action:
            threshold = value_limits.get("creation_threshold")
            if threshold and resource["value"] > threshold:
                return False, f"Value {resource['value']} exceeds creation threshold {threshold}"
        
        if action and "approve" in action:
            threshold = value_limits.get("approval_threshold")
            if threshold and resource["value"] > threshold:
                return False, f"Value {resource['value']} exceeds approval threshold {threshold}"
    
    return True, "Within access scope"

def matches_user_attributes(user, policy_user_attrs: Dict) -> bool:
    """Check if user matches the policy's user attribute requirements"""
    for attr_name, required_value in policy_user_attrs.items():
        if hasattr(user, attr_name):
            user_value = getattr(user, attr_name)
        else:
            # Computed attributes
            if attr_name == "is_accounting_officer":
                user_value = user.is_accounting_officer
            elif attr_name == "roles":
                user_value = [user.role.name] if user.role else []
            elif attr_name == "position_title":
                user_value = user.position_title
            else:
                return False 
        
        # Compare values
        if isinstance(required_value, list):
            if isinstance(user_value, list):
                if not any(val in required_value for val in user_value):
                    return False
            else:
                if user_value not in required_value:
                    return False
        else:
            if user_value != required_value:
                return False
    
    return True

def matches_resource_attributes(resource: Optional[Dict], policy_resource_attrs: Dict) -> bool:
    """Check if resource matches the policy's resource attribute requirements"""
    if not resource:
        return not policy_resource_attrs
    
    for attr_name, required_value in policy_resource_attrs.items():
        if attr_name not in resource:
            return False
        
        resource_value = resource[attr_name]
        
        # Handle comparison operators
        if isinstance(required_value, dict):
            for operator, threshold in required_value.items():
                if operator == ">=" and resource_value < threshold:
                    return False
                elif operator == "<=" and resource_value > threshold:
                    return False
                elif operator == ">" and resource_value <= threshold:
                    return False
                elif operator == "<" and resource_value >= threshold:
                    return False
                elif operator == "==" and resource_value != threshold:
                    return False
        elif isinstance(required_value, list):
            if resource_value not in required_value:
                return False
        else:
            if resource_value != required_value:
                return False
    
    return True

def evaluate_abac_policies(user, action: str, resource: Optional[Dict], db: Session) -> Tuple[str, Optional[str]]:
    applicable_policies = (
        db.query(ABACPolicy).filter(

            ABACPolicy.is_active == True,
            ABACPolicy.action_names.contains([action]) 
        ).order_by(ABACPolicy.priority.desc()).all()
    )
    
    deny_policies = []
    allow_policies = []
    
    for policy in applicable_policies:
        if not matches_user_attributes(user, policy.user_attributes):
            continue
        
        if not matches_resource_attributes(resource, policy.resource_attributes):
            continue
            
        if policy.effect.value == "DENY":
            deny_policies.append(policy)
        else:
            allow_policies.append(policy)
    
    # DENY policies override ALLOW policies
    if deny_policies:
        policy = deny_policies[0]  # Highest priority deny
        logger.warning(f"DENY policy {policy.id} matched for user {user.id}, action {action}")
        return "DENY", f"Policy denied: {policy.description}"
    
    if allow_policies:
        policy = allow_policies[0]  # Highest priority allow
        logger.info(f"ALLOW policy {policy.id} matched for user {user.id}, action {action}")
        return "ALLOW", f"Policy allowed: {policy.description}"

    return "ALLOW", "No policy restrictions"

def check_full_permission(user, resource_type: str, action: str, db: Session,
                      resource: Optional[Dict] = None) -> bool:
    """Main checker that combines all three layers"""
    full_action = f"{resource_type}.{action}"
    

    # Layer 1: Role-based permission check
    role_allowed, role_reason = check_role_permission(user, full_action)
    if not role_allowed:
        logger.warning(f"RBAC denied for user {user.id}: {role_reason}")
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied - Role: {role_reason}"
        )
 
    # Layer 2: Access scope check
    scope_allowed, scope_reason = check_access_scope(user, resource, full_action)
    if not scope_allowed:
        logger.warning(f"Scope denied for user {user.id}: {scope_reason}")
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied - Scope: {scope_reason}"
        )
    
    # Layer 3: ABAC policy evaluation
    policy_effect, policy_reason = evaluate_abac_policies(user, full_action, resource, db)
    if policy_effect == "DENY":
        logger.warning(f"Policy denied for user {user.id}: {policy_reason}")
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied - Policy: {policy_reason}"
        )
    
    logger.info(f"Permission granted for user {user.id}, action {full_action}")
    return True
#----------------------------------------------------      
    # except HTTPException:
    #     raise 
    # except Exception as e:
    #     logger.error(f"Error checking permissions for user {user.id}: {str(e)}")
    #     raise HTTPException(
    #         status_code=500, 
    #         detail=f"Internal error during permission check :  {str(e)}"
    #     )

def check_simple_permission(user, resource_type: str, action: str) -> bool:
    full_action = f"{resource_type}.{action}"
    role_allowed, _ = check_role_permission(user, full_action)
    return role_allowed

def apply_scope_filter(db: Session, query: Query, user: User, resource_type: str) -> Query:
    scope = get_merged_scope(user)
    
    if resource_type == "asset":
        # Department filtering - skip if user can access all departments
        allowed_deps = scope.get("departments", [])
        if allowed_deps and "*" not in allowed_deps:
            query = query.filter(Assets.department_id.in_(allowed_deps))
        
        # Geo filtering
        allowed_counties = scope.get("geographic", [])
        if allowed_counties:
            county_filters = []
            for county in allowed_counties:
                county_filter = Assets.location.op('->>')('county_name').ilike(f'%{county}%')
                county_filters.append(county_filter)
            if county_filters:
                query = query.filter(db.or_(*county_filters))
        
        # Category filtering
        allowed_categories = scope.get("asset_categories", [])
        if allowed_categories and "*" not in allowed_categories:
            query = query.filter(Assets.category.in_(allowed_categories))
    
    return query

def build_asset_resource(asset: Assets) -> Dict:
    """Build resource dictionary for asset operations"""
    resource = {
        "category": asset.category.value if asset.category else None,
        "department": asset.department_id,
        "value": float(asset.current_value or asset.acquisition_cost or 0),
        "status": asset.status.value if asset.status else None
    }
    
    # Extract county from asset location
    if asset.location and isinstance(asset.location, dict):
        county_name = asset.location.get("county_name")
        if county_name:
            resource["county"] = county_name.lower().replace(" ", "_")
    
    return resource

def checkif_accounting_officer(user) -> bool:
    """Check if user is accounting officer"""
    if not user.is_accounting_officer:
        raise HTTPException(
            status_code=403, 
            detail="This action requires an Accounting Officer"
        )
    return True

def require_specific_role(user, required_roles: List[str]) -> Tuple[bool, str]:
    """Check if user has one of the specified roles, check only name of role"""
    if not user.role or user.role.name not in required_roles:
        detail = (f"This action requires one of these roles: {', '.join(required_roles)}" if debugging else f"not enough permissions")
        return False, detail
    return True ,f"allowed"