import asyncio
import json
import logging
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Set up basic logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow every origin
    allow_credentials=False,  # Credentials must be false when allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store the currently active program
active_program = None

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/start")
async def start_program(request: Request):
    """
    Start a tracking or game program.
    Expected JSON body: { "program": "<program_name>" }
    """
    global active_program
    body = await request.json()
    program = body.get("program")
    if not program:
        return JSONResponse(
            status_code=400, content={"error": "Program not specified"}
        )

    active_program = program
    logging.info(f"Starting program: {program}")

    try:
        if program == "eye_tracking_control":
            import eye
            if hasattr(eye, "start_tracking"):
                eye.start_tracking()
        elif program == "eye_tracking_game":
            import eyegame
            if hasattr(eyegame, "start_game"):
                eyegame.start_game()
        elif program == "hand_tracking_control":
            # Use hands1.py instead of hand.py for hand detection.
            import hand1
            if hasattr(hand1, "start_tracking"):
                hand1.start_tracking()
        elif program == "hand_tracking_game":
            import gesturegame
            if hasattr(gesturegame, "start_game"):
                gesturegame.start_game()
        else:
            logging.warning(f"Unknown program: {program}")
            return JSONResponse(
                status_code=400, content={"error": "Unknown program"}
            )
    except Exception as e:
        logging.error(f"Error starting program {program}: {e}")
        return JSONResponse(
            status_code=500, content={"error": f"Error starting program: {str(e)}"}
        )

    return {"message": f"Program {program} started"}

@app.post("/terminate")
async def terminate_program(request: Request):
    """
    Terminate the currently running program.
    Expected JSON body: { "program": "<program_name>" }
    """
    global active_program
    body = await request.json()
    program = body.get("program")
    if active_program != program:
        return JSONResponse(
            status_code=400, content={"error": "Program mismatch or no active program"}
        )

    logging.info(f"Terminating program: {program}")
    try:
        if program == "eye_tracking_control":
            import eye
            if hasattr(eye, "terminate_tracking"):
                eye.terminate_tracking()
        elif program == "eye_tracking_game":
            import eyegame
            if hasattr(eyegame, "terminate_game"):
                eyegame.terminate_game()
        elif program == "hand_tracking_control":
            import hand1
            if hasattr(hand1, "terminate_tracking"):
                hand1.terminate_tracking()
        elif program == "hand_tracking_game":
            import gesturegame
            if hasattr(gesturegame, "terminate_game"):
                gesturegame.terminate_game()
        else:
            logging.warning(f"Unknown program: {program}")
            return JSONResponse(
                status_code=400, content={"error": "Unknown program"}
            )
    except Exception as e:
        logging.error(f"Error terminating program {program}: {e}")
        return JSONResponse(
            status_code=500, content={"error": f"Error terminating program: {str(e)}"}
        )

    active_program = None
    return {"message": f"Program {program} terminated"}

@app.websocket("/ws/tracking")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint to stream real-time tracking data.
    Expects an initial JSON message with the program info.
    """
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        init_data = json.loads(data)
        program = init_data.get("program")
        logging.info(f"WebSocket connection initiated for program: {program}")

        while True:
            tracking_data = {
                "eye": {
                    "x": round(random.uniform(-1, 1), 2),
                    "y": round(random.uniform(-1, 1), 2)
                },
                "hand": {
                    "x": round(random.uniform(-1, 1), 2),
                    "y": round(random.uniform(-1, 1), 2),
                    "z": round(random.uniform(-1, 1), 2),
                    "gestures": []
                }
            }
            if random.random() > 0.8:
                tracking_data["hand"]["gestures"].append(random.choice(["pinch", "grab", "point"]))
            await websocket.send_text(json.dumps(tracking_data))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")
    except Exception as e:
        logging.error(f"Error in WebSocket connection: {e}")
        await websocket.close()

# Control panel configuration endpoint
control_panel_programs = [
    {"id": "eye_tracking_control", "name": "Eye Tracking Control", "description": "Control cursor with your eyes"},
    {"id": "eye_tracking_game", "name": "Eye Tracking Game", "description": "Play games with eye movements"},
    {"id": "hand_tracking_control", "name": "Hand Tracking Control", "description": "Control cursor with hand gestures"},
    {"id": "hand_tracking_game", "name": "Hand Tracking Game", "description": "Play games with hand gestures"},
]

@app.get("/api/control-panel")
async def get_control_panel():
    return {"programs": control_panel_programs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
