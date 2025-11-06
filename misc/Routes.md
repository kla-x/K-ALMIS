Roles
POST /api/v1/roles/no-auth-crit - Create Role Noperm
GET /api/v1/roles/ - List Roles
POST /api/v1/roles/ - Create Role
GET /api/v1/roles/{role_id} - Get Role
PUT /api/v1/roles/{role_id} - Update Role
DELETE /api/v1/roles/{role_id} - Delete Role
GET /api/v1/roles/{role_id}/permissions - Get Role Permissions
POST /api/v1/roles/{role_id}/permissions/add - Add Permission
POST /api/v1/roles/{role_id}/permissions/remove - Remove Permission
GET /api/v1/roles/user/{role_id} - Get All Users With Role

Users
GET /api/v1/users/ - Get All Users Param
POST /api/v1/users/ - Create New User Adm
GET /api/v1/users/me - Get My Profile
PUT /api/v1/users/me - Patch My Profile
GET /api/v1/users/me/permissions - Get My Allowd Permissions
GET /api/v1/users/me/permissions/{resource} - Get My Allowed Actions For Resource
GET /api/v1/users/{user_id}/permissions - Get User Permissions Adm
PUT /api/v1/users/{user_id}/permissions - Give User Permissions Adm
GET /api/v1/users/{user_id}/permissions/{resource} - Get User Permissions By Resource Adm
GET /api/v1/users/{user_id} - Get User Details
PUT /api/v1/users/{user_id} - Patch User Details Adm
DELETE /api/v1/users/{user_id} - Delete User
PUT /api/v1/users/{user_id}/status - Patch User Status


Authentication
POST /api/v1/auth/register - User Register
POST /api/v1/auth/login - Login
POST /api/v1/auth/login/oauth2form - Login Oauth2
POST /api/v1/auth/logout - Logout
GET /api/v1/auth/protected - Protected Route Test
POST /api/v1/auth/refresh - Refresh Token
POST /api/v1/auth/change-password - Prifile Change Password
POST /api/v1/auth/request-password-reset - Request Password Reset
GET /api/v1/auth/password-reset - Check Password Reset Token
POST /api/v1/auth/password-reset - Reset Password
GET /api/v1/auth/me - Get My Profile

locations
GET /api/v1/locations/counties/ - Get Counties
GET /api/v1/locations/counties/{county_identifier}/ - Get County Constituencies
GET /api/v1/locations/counties/{county_identifier}/constituencies/ - constituency_name}/
Get Constituency Wards
GET /api/v1/locations/counties/{county_identifier}/tree/ - Get County Tree
GET /api/v1/locations/search/ - Search Locations
GET /api/v1/locations/coordinates/reverse/ - Reverse Geocode
GET /api/v1/locations/search/geocode/ - Forward Geocode

Departments
GET /api/v1/departments/ - List All Departments
POST /api/v1/departments/ - Create Department
GET /api/v1/departments/simple - List All Departments Simple
GET /api/v1/departments/public - List All Departments Public
GET /api/v1/departments/{dep_id}/users - Get Department Members
GET /api/v1/departments/{dep_id}/assets - Get Department Assets Dummy
GET /api/v1/departments/{dep_id}/hierarchy - Get Department Hierachy
POST /api/v1/departments/{dep_id}/status - Change Department Status
GET /api/v1/departments/{dep_id} - Get Department By Id
DELETE /api/v1/departments/{dep_id} - Delete A Department
PUT /api/v1/departments/{dep_id} - Patch Department Details

Assets CRUD
POST /api/v1/assets/ - Create A New Asset
GET /api/v1/assets/ - List Assets Search Func
GET /api/v1/assets/categories - List Asset Categories Simple
GET /api/v1/assets/{asset_id} - Get Asset By Id
PUT /api/v1/assets/{asset_id} - Update Asset
DELETE /api/v1/assets/{asset_id} - Delete Asset
PATCH /api/v1/assets/{asset_id}/status - Update Asset Status
GET /api/v1/assets/search/advanced - Advanced Asset Search Adm

Assets Supporting routes
GET /api/v1/assets/supp/assetstatus - List Asset Statuses
GET /api/v1/assets/supp/assetcondition - List Asset Condition
GET /api/v1/assets/supp/categories/newlist - List Categories Byname
GET /api/v1/assets/supp/categories/detailed - List Asset Categories Detailed
GET /api/v1/assets/supp/categories/info - Get Asset Categories Info
GET /api/v1/assets/supp/maintain/MaintenanceType - List Maintainance Types
GET /api/v1/assets/supp/maintain/IssueCategory - List Issue Categories
GET /api/v1/assets/supp/maintain/PriorityLevel - List Priorrity Levels
GET /api/v1/assets/supp/maintain/SeverityLevel - List Severerity Level
GET /api/v1/assets/supp/maintain/maintainanceoutcome - List The 2 Maint Outcomes

Assets Lifecycle
POST /api/v1/assets/life/{asset_id}/activate - Activate Asset
POST /api/v1/assets/life/{asset_id}/deactivate - Deactivate Asset
POST /api/v1/assets/life/{asset_id}/mark-disposal - Mark Asset For Disposal
GET /api/v1/assets/life/{asset_id}/lifecycle - Get Asset Lifecycle Adm

Assets Tracking
POST /api/v1/assets/{asset_id}/generate-qr - Generate Asset Qr Code
PUT /api/v1/assets/{asset_id}/location - Update Asset Location
GET /api/v1/assets/by-tag/{tag_number} - Get Asset By Tag No
GET /api/v1/assets/by-barcode/{barcode} - Get Asset By Barcode
GET /api/v1/assets/by-serial/{serial_number} - Get Asset By Serial No

Assets Assignment
POST /api/v1/assets/{asset_id}/assign - Assign User An Asset
DELETE /api/v1/assets/{asset_id}/unassign - Unassign Asset From Usr
PUT /api/v1/assets/{asset_id}/reassign - Reassign An Asset To User
GET /api/v1/assets/{asset_id}/assignment-history - Get Assignment Hist
GET /api/v1/assets/m/myassets - List User Assigned Assets
GET /api/v1/assets/assignments/all - List All Assignments
GET /api/v1/assets/assignments/unassigned - List Unassigned Assets

Assets Transfers
POST /api/v1/transfers/initiate - Transfer An Asset
GET /api/v1/transfers/ - List Transfers Param
GET /api/v1/transfers/{trans_id} - Get Transfer By Id
POST /api/v1/transfers/{trans_id}/approve - Approve A Transfer
POST /api/v1/transfers/{trans_id}/complete - Approve A Transfer
POST /api/v1/transfers/{asset_id}/history - Get Asset Transfer Hist
POST /api/v1/transfers/{trans_id}/reject - Reject Transfer Request
POST /api/v1/transfers/{trans_id}/cancel - Cancel A Transfer Request
GET /api/v1/transfers/pending - List All Pending Transfers
GET /api/v1/transfers/by-user/{user_id} - Show All User Transers

Assets Maintainance
POST /api/v1/assets/{asset_id}/maintenance/initiate - Init Maint Req
POST /api/v1/assets/{asset_id}/maintenance/schedule - Schedule Maint
POST /api/v1/assets/{asset_id}/maintenance/approve - Approve Maint
POST /api/v1/assets/{asset_id}/maintenance/start - Start Maint
POST /api/v1/assets/{asset_id}/maintenance/complete - Complete Maint
GET /api/v1/assets/{asset_id}/maintenance/history - Get Maint Hist
GET /api/v1/assets/maintenance/upcoming - Get Upcoming Maint

Assets Disposal
POST /api/v1/assets/{asset_id}/disposal/initiate - Init Disposal
POST /api/v1/assets/{asset_id}/disposal/schedule - Schedule Disposal
POST /api/v1/assets/{asset_id}/disposal/approve - Approve Disposal
POST /api/v1/assets/{asset_id}/disposal/execute - Execute Disposal
POST /api/v1/assets/{asset_id}/disposal/undo - Undo Disposal
GET /api/v1/assets/disposals - Get All Disposals
GET /api/v1/assets/{asset_id}/disposal/history - Get Disposal Hist

sset Reports Utils
GET /api/v1/r/reports/asset-age-analysis - Get Asset Age Analysis Report
GET /api/v1/r/reports/department-comparison - Get Department Comparison Report
GET /api/v1/r/reports/asset-utilization - Get Asset Utilization Report
GET /api/v1/r/reports/maintenance-cost-analysis - Get Maintenance Cost Analysis Report
GET /api/v1/r/reports/available-reports - List Available Reports

Asset Reports general
GET /api/v1/reports/assets-summary - Get Assets Summary Report
GET /api/v1/reports/department-assets/{dept_id} - Get Department Asset Report
GET /api/v1/reports/assets-by-condition - Get Assets By Condition Report
GET /api/v1/reports/depreciation-report - Get Depreciation Report
GET /api/v1/reports/category-specific-report/{category} - Get Category Specific Report

Asset Basic Reports
GET /api/v1/r/reports/asset-summary-dashboard - Get Asset Summary Dashboard
GET /api/v1/r/reports/depreciation - Get Depreciation Report
GET /api/v1/r/reports/asset-status-condition - Get Asset Status Condition Report
GET /api/v1/r/reports/category-specific/{category} - Get Category Specific Report
GET /api/v1/r/reports/unassigned-assets - Get Unassigned Assets Report

Asset Departments Reports
GET /api/v1/r/reports/department-assets/{dept_id} - Get Department Asset Report
GET /api/v1/r/reports/user-responsibility - Get User Responsibility Report

Asset Maintainance Reports
GET /api/v1/r/reports/maintenance-summary - Get Maintenance Summary Report
GET /api/v1/r/reports/upcoming-maintenance - Get Upcoming Maintenance Report
GET /api/v1/r/reports/maintenance-backlog - Get Maintenance Backlog Report

Asset Transfers n Disposals Reports
GET /api/v1/r/reports/pending-transfers-disposals - Get Pending Transfers Disposals Report
GET /api/v1/r/reports/transfer-disposal-history - Get Transfer Disposal History Report

Asset Executive Reports
GET /api/v1/r/reports/executive-summary - Get Executive Summary Report

Asset Complience Reports
GET /api/v1/r/reports/missing-data - Get Missing Data Report
GET /api/v1/r/reports/geographic-distribution - Get Geographic Distribution Report

Asset Security Reports
GET /api/v1/r/reports/activity-log - Get Activity Log Report
GET /api/v1/r/reports/failed-login-attempts - Get Failed Login Report
GET /api/v1/r/reports/data-modifications - Get Data Modification Audit Report
