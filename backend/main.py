import uvicorn

if __name__ == "__main__":
    # This remains for backward compatibility with existing launch commands
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
