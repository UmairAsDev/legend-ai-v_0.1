from controller.route.app import router as app_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware





app = FastAPI()
app.include_router(app_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def main():
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    
    
    
if __name__ == "__main__":
    main()