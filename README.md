## End to End Traffic Violation Detection System

### Setup
- Clone the repository
- Install dependencies: `pip install -r requirements.txt`
- Set up MySQL database
- Run the application: `python -m app.realtime_webcam` or `python -m app.realtime`

### Running FastAPI Server
To run the FastAPI server using uvicorn:

1. **Start the server:**
   ```bash
   uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Alternative command (from project root):**
   ```bash
   python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the API:**
   - API Base URL: `http://localhost:8000`
   - Interactive API docs: `http://localhost:8000/docs`
   - Alternative docs: `http://localhost:8000/redoc`

4. **Available endpoints:**
   - `GET /detections` - Retrieve all traffic violation detections
   - `GET /image/{detection_id}` - Get violation image by ID
   - `GET /predict` - Run traffic violation prediction

**Note:** Ensure MySQL database is running and configured before starting the FastAPI server.

### Steps to start MySQL

1. Install Complete MySQL Server with Workbench from Offical MySQL Website

2. **Start MySQL server:**
   ```bash
   net start MySQL80
   ```
   **Note:** Replace MySQL80 with your MySQL server name if different, to check server name use `net start` on cmd

3. **Verify MySQL status:**
   ```bash
   sudo service mysql status
   ```

### Realtime Webcam
- Run `python -m app.realtime_webcam`
- The application will start and display the webcam feed
- The application will detect traffic violations and display the results
- The application will save the results to a MySQL database

### Realtime Video
- Run `python -m app.realtime`
- The application will start and display the video feed
- The application will detect traffic violations and display the results
- The application will save the results to a MySQL database

