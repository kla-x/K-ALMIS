from fastapi import FastAPI
from .database import  engine
from . import models
from .services.logger_queue import setup_background_logging
from .system_vars import sys_logger

from .routers import a_crude, auth,roles,users,departments,location,a_transfer,a_supp_routes,a_lifecycle,a_tracking,a_assignment,a_maintainance,a_disposal
from .routers.reports import assets_r,complience_r,departments_r,exec_r,maintainance_r,reports,sec_r,transdispo_r,utils_r
from fastapi.middleware.cors import CORSMiddleware

from .routers import other_supp_routes,auth22



app = FastAPI()

if sys_logger:
    setup_background_logging(app)
 
models.Base.metadata.create_all(bind=engine)


origins = [
    "http://localhost:8080",
    "http://localhost:5173"
] # also mig

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) # migrate to sys vars
'''
td:
 - load counties in memory during startup

'''
app.include_router(roles.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(auth22.router)

app.include_router(location.router)
app.include_router(departments.router)

app.include_router(a_crude.router)
app.include_router(other_supp_routes.router)
app.include_router(a_supp_routes.router)
app.include_router(a_lifecycle.router)
app.include_router(a_tracking.router)
app.include_router(a_assignment.router)
app.include_router(a_transfer.router)

app.include_router(a_maintainance.router)
app.include_router(a_disposal.router)

app.include_router(utils_r.router)
app.include_router(reports.router)
app.include_router(assets_r.router)
app.include_router(departments_r.router)
app.include_router(maintainance_r.router)
app.include_router(transdispo_r.router)
app.include_router(exec_r.router)
app.include_router(complience_r.router)
app.include_router(sec_r.router)