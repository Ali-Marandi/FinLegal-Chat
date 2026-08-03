from app import app

if __name__ == "__main__":
    print("Starting FinLegal Chat Server...")
    app.run(host='0.0.0.0', port=5000)
