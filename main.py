import uuid
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from collections import defaultdict

# Import our local DB logic and CRUD operations
from database import init_db
import crud

app = FastAPI(title="CivicConnect V2")

# ==========================================
# 1. APP CONFIGURATION & SETUP
# ==========================================

# Mount Static Files & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Session Middleware (Required for Login & Upvotes)
app.add_middleware(SessionMiddleware, secret_key="super-secret-fastapi-key")

# Database Initialization on Startup
@app.on_event("startup")
def on_startup():
    init_db()
    
    # Auto-cleanup: Delete resolved issues older than 60 days
    deleted_count = crud.delete_old_resolved_issues(days=60)
    print(f"Startup Maintenance: Deleted {deleted_count} old resolved issues.")

# ==========================================
# 2. UTILITY FUNCTIONS
# ==========================================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def is_allowed_file(filename: str):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Custom Jinja Filter: Check if issue is overdue (30+ days and not resolved)
def is_overdue(issue):
    if issue['status'] == 'Resolved':
        return False
    try:
        # Check if issue is dict (from crud) or Row
        created_at_str = issue['created_at']
        created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
        return datetime.now() > created_at + timedelta(days=30)
    except:
        return False

templates.env.filters['is_overdue'] = is_overdue

# ==========================================
# 3. API ROUTES (AJAX / JSON)
# ==========================================

@app.get("/api/check_duplicates")
async def check_duplicates(area: str = "", title: str = ""):
    # 1. Safety Check: Return empty if no data provided
    if not area or not title:
        return JSONResponse(content=[])

    results = crud.check_duplicate_issues(area, title)
    return JSONResponse(content=results)

# ==========================================
# 4. PUBLIC ROUTES
# ==========================================

# HOME PAGE (Feed)
@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request, 
    area: str = None, 
    status: str = None,
    q: str = None
):
    issues = crud.get_issues(area, status, q)
    
    # Fetch User Votes (for button coloring)
    user_votes = []
    if 'user_id' in request.session:
        user_votes = crud.get_user_votes(request.session['user_id'])
        
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "issues": issues,
        "current_area": area,
        "current_status": status,
        "user_votes": user_votes,
        "search_query": q
    })

# STATS PAGE (Analytics)
@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    
    # 1. KPIs
    total = crud.get_total_issues_count()
    resolved = crud.get_resolved_issues_count()
    rate = round((resolved/total)*100, 1) if total > 0 else 0

    # 2. Area Analysis (Pie Chart)
    area_data = crud.get_area_stats()
    area_labels = [row['area'] for row in area_data]
    area_counts = [row['count'] for row in area_data]

    # 3. Monthly Trends (Bar Chart)
    # Using SQL grouping for efficiency
    trend_data = crud.get_monthly_trend_data()
    
    # Reverse to show Jan -> Feb (SQL DESC returns newest first)
    months = [row['month'] for row in trend_data][::-1]
    chart_raised = [row['total_count'] for row in trend_data][::-1]
    chart_resolved = [row['resolved_count'] for row in trend_data][::-1]

    # 4. Top Critical Issues
    top_issues = crud.get_top_critical_issues()
    
    stats = {
        "kpi": { "total": total, "resolved": resolved, "rate": rate },
        "chart": { 
            "labels": months,
            "raised": chart_raised, 
            "resolved": chart_resolved
        },
        "area_chart": {
            "labels": area_labels,
            "data": area_counts
        },
        "top_issues": top_issues
    }

    return templates.TemplateResponse("stats.html", {
        "request": request,
        "stats": stats
    })

# SUBMIT PAGE (GET)
@app.get("/submit", response_class=HTMLResponse)
async def submit_page(request: Request):
    # Fetch coordinates of all issues (Ignore ones without GPS)
    existing_issues = crud.get_issues_with_location()
    
    return templates.TemplateResponse("submit.html", {
        "request": request, 
        "existing_issues": existing_issues
    })

# SUBMIT ACTION (POST)
@app.post("/submit")
async def submit_issue(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    area: str = Form(...),
    latitude: str = Form(None),
    longitude: str = Form(None),
    image: UploadFile = File(None)
):
    filename = None
    
    # 1. Handle Optional Image
    if image and image.filename:
        if is_allowed_file(image.filename):
            clean_name = f"{uuid.uuid4().hex}_{image.filename}"
            file_path = os.path.join(UPLOAD_FOLDER, clean_name)
            with open(file_path, "wb") as buffer:
                content = await image.read()
                buffer.write(content)
            filename = clean_name
    
    # 2. Handle Optional Map Data
    if not latitude or latitude == "":
        latitude = None
    if not longitude or longitude == "":
        longitude = None

    crud.create_issue(title, description, area, latitude, longitude, filename)
    
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# UPVOTE ACTION
@app.post("/upvote/{issue_id}")
async def upvote(request: Request, issue_id: int):
    if 'user_id' not in request.session:
        request.session['user_id'] = str(uuid.uuid4())
    
    user_id = request.session['user_id']
    crud.toggle_vote(user_id, issue_id)
    
    # Redirect back to the previous page (Feed or Details)
    referer = request.headers.get("referer")
    if referer:
        return RedirectResponse(url=referer, status_code=303)
        
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# ==========================================
# 5. ADMIN ROUTES
# ==========================================

# LOGIN PAGE
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# LOGIN ACTION
@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    # Hardcoded check for MVP
    if username == "admin" and password == "password":
        request.session['admin_user'] = username
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "error": "Invalid Credentials"
    })

# LOGOUT ACTION
@app.get("/logout")
async def logout(request: Request):
    request.session.pop('admin_user', None)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

# DASHBOARD (Admin Home)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if 'admin_user' not in request.session:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    issues = crud.get_issues()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "issues": issues
    })

# MANAGE ISSUE (GET - Case File View)
@app.get("/issue/{issue_id}/manage", response_class=HTMLResponse)
async def manage_issue_page(request: Request, issue_id: int):
    if not request.session.get('admin_user'):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    issue = crud.get_issue_by_id(issue_id)
    
    if not issue:
        return "Issue not found", 404
        
    return templates.TemplateResponse("manage_issue.html", {
        "request": request, 
        "issue": issue
    })

# PUBLIC ISSUE DETAILS (GET)
@app.get("/issue/{issue_id}", response_class=HTMLResponse)
async def issue_detail_page(request: Request, issue_id: int):
    issue = crud.get_issue_by_id(issue_id)
    
    if not issue:
        return "Issue not found", 404
        
    return templates.TemplateResponse("issue_detail.html", {
        "request": request,
        "issue": issue
    })

# MANAGE ISSUE (POST - Update Status)
@app.post("/issue/{issue_id}/manage")
async def update_issue_status(
    request: Request, 
    issue_id: int, 
    status: str = Form(...),
    resolved_image: UploadFile = File(None)
):
    if not request.session.get('admin_user'):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # 1. Handle Proof Image
    filename = None
    if resolved_image and resolved_image.filename:
        if is_allowed_file(resolved_image.filename):
            clean_name = f"resolved_{uuid.uuid4().hex}_{resolved_image.filename}"
            file_path = os.path.join(UPLOAD_FOLDER, clean_name)
            with open(file_path, "wb") as buffer:
                content = await resolved_image.read()
                buffer.write(content)
            filename = clean_name
            
    # 2. Update Status
    crud.update_issue_status(issue_id, status, filename)
    
    # Redirect to Dashboard (Using 303 directly)
    return RedirectResponse(url="/dashboard", status_code=303)