import uvicorn
from env.server import app

def main():
    """Main entry point for starting the Gatekeeper OpenEnv server."""
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
