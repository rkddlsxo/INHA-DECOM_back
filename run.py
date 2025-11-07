import os
from app import create_app, scheduler 

app = create_app()

if __name__ == '__main__':

    with app.app_context():
        scheduler.start()
    print("[INFO] APScheduler started (Production Mode)...")

    app.run(debug=False, port=5050)