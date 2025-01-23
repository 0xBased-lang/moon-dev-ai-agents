from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
import uvicorn
from pathlib import Path
import sys
import os
import json
from dotenv import load_dotenv
import datetime

# Load environment variables
load_dotenv()

# Verify required environment variables
required_vars = [
    "DEEPSEEK_KEY",
    "PORT"  # Heroku provides PORT
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print("❌ Missing required environment variables:", missing_vars)
    print("Please set these in your .env file or Heroku config vars")
    sys.exit(1)

print("✅ All required environment variables found!")

# Get the current directory
FRONTEND_DIR = Path(__file__).parent
PROJECT_ROOT = FRONTEND_DIR.parent

# Add src directory to Python path
sys.path.append(str(PROJECT_ROOT))

from agents.rbi_agent import process_trading_idea

app = FastAPI(
    title="Moon Dev's RBI Agent 🌙",
    description="Research-Backtest-Implement Trading Strategies with AI",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

# Templates
templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))

# Global variable to store results
processing_results = []
is_processing_complete = False

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Moon Dev's RBI Agent 🌙"}
    )

async def process_strategy_background(links: list):
    """Process strategies in the background"""
    global processing_results, is_processing_complete
    
    try:
        processing_results = []
        is_processing_complete = False
        
        for i, link in enumerate(links, 1):
            try:
                print(f"🌙 Processing Strategy {i}: {link}")
                
                # Get the latest strategy and backtest files
                strategy_dir = PROJECT_ROOT / "data/rbi/research"
                backtest_dir = PROJECT_ROOT / "data/rbi/backtests_final"
                
                # Clear old files to prevent using cached results
                print("🧹 Clearing old files...")
                for file in strategy_dir.glob("strategy_*.txt"):
                    print(f"  🗑️ Removing old strategy file: {file.name}")
                    file.unlink()
                for file in backtest_dir.glob("backtest_final_*.py"):
                    print(f"  🗑️ Removing old backtest file: {file.name}")
                    file.unlink()
                
                # Process the strategy
                process_trading_idea(link)
                
                # Get the most recent files
                strategy_files = sorted(strategy_dir.glob("strategy_*.txt"), key=lambda x: x.stat().st_mtime, reverse=True)
                backtest_files = sorted(backtest_dir.glob("backtest_final_*.py"), key=lambda x: x.stat().st_mtime, reverse=True)
                
                if strategy_files and backtest_files:
                    with open(strategy_files[0], 'r') as f:
                        strategy_content = f.read()
                    with open(backtest_files[0], 'r') as f:
                        backtest_content = f.read()
                    
                    result = {
                        "strategy_number": i,
                        "link": link,
                        "strategy": strategy_content,
                        "backtest": backtest_content,
                        "strategy_file": str(strategy_files[0].name),
                        "backtest_file": str(backtest_files[0].name),
                        "status": "success"
                    }
                else:
                    result = {
                        "strategy_number": i,
                        "link": link,
                        "error": "Strategy processing completed but couldn't find output files",
                        "status": "error"
                    }
                
                processing_results.append(result)
                
            except Exception as e:
                print(f"❌ Error processing strategy {i}: {e}")
                processing_results.append({
                    "strategy_number": i,
                    "link": link,
                    "error": f"Error processing strategy: {str(e)}",
                    "status": "error"
                })
        
        is_processing_complete = True
        
    except Exception as e:
        print(f"❌ Error processing strategies: {e}")
        is_processing_complete = True

@app.post("/analyze")
async def analyze_strategy(request: Request, background_tasks: BackgroundTasks):
    try:
        form = await request.form()
        links = form.get("links", "").split(",")
        links = [link.strip() for link in links if link.strip()]
        
        if not links:
            return {"status": "error", "message": "No links provided"}
            
        print("🌙 Starting strategy analysis...")
        
        # Add the processing task to background tasks
        background_tasks.add_task(process_strategy_background, links)
        
        return {"status": "success", "message": "Analysis started in background"}
        
    except Exception as e:
        print(f"❌ Error in analyze_strategy: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/download/strategy/{filename}")
async def download_strategy(filename: str):
    """Download a strategy file"""
    file_path = PROJECT_ROOT / "data/rbi/research" / filename
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/plain"
        )
    return JSONResponse({
        "status": "error",
        "message": "File not found"
    })

@app.get("/download/backtest/{filename}")
async def download_backtest(filename: str):
    """Download a backtest file"""
    file_path = PROJECT_ROOT / "data/rbi/backtests_final" / filename
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/plain"
        )
    return JSONResponse({
        "status": "error",
        "message": "File not found"
    })

@app.get("/results")
async def get_results():
    """Get current processing results"""
    return {
        "status": "success",
        "results": processing_results,
        "complete": is_processing_complete
    }

if __name__ == "__main__":
    # Get port from environment variable (Heroku sets this)
    port = int(os.getenv("PORT", 8000))
    
    print("🌙 Moon Dev's RBI Agent Starting...")
    print(f"📁 Frontend Directory: {FRONTEND_DIR}")
    print(f"📁 Static Files: {FRONTEND_DIR / 'static'}")
    print(f"📁 Templates: {FRONTEND_DIR / 'templates'}")
    
    # Start server with host 0.0.0.0 for Heroku
    uvicorn.run("main:app", host="0.0.0.0", port=port) 