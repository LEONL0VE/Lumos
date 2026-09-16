"""Server for interfacing with the frontend.
"""
import os
from pathlib import Path

import pandas as pd
import socketio
from aiohttp import web
from aiohttp_index import IndexMiddleware

import bias
import bias_util

# Set the path for the Google Cloud Logging logger
currdir = Path(__file__).parent.absolute()

CLIENTS = {}  # entire data map of all client data
CLIENT_PARTICIPANT_ID_SOCKET_ID_MAPPING = {}
CLIENT_SOCKET_ID_PARTICIPANT_MAPPING = {}
COMPUTE_BIAS_FOR_TYPES = [
    "mouseout_item",
    "mouseout_group",
    "click_group",
    "click_add_item",
    "click_remove_item",
]

SIO = socketio.AsyncServer(cors_allowed_origins='*', cookie=None)
APP = web.Application(middlewares=[IndexMiddleware()])
SIO.attach(APP)

async def handle_ui_files(request):
    # Extract the requested file name
    fname = request.match_info.get('fname', 'index.html')

    # Serve index.html for all routes that don't have a file extension
    if '.' not in fname:
        fname = 'index.html'

    # Define the public directory (similar to Flask's 'public' directory)
    public_dir = os.path.join(os.path.dirname(__file__), 'public')

    # Serve the file from the public directory
    file_path = os.path.join(public_dir, fname)

    try:
        return web.FileResponse(file_path)
    except FileNotFoundError:
        raise web.HTTPNotFound()

# Static file serving
APP.router.add_static('/static/', path=str(os.path.join(os.path.dirname(__file__), 'public')), name='static')

# Dynamic routing for all paths, similar to Flask's catch-all routes
APP.router.add_route('GET', '/{fname:.*}', handle_ui_files)

@SIO.event
async def connect(sid, environ):
    print(f"Connected: {sid}")
    attr_dist = {}
    for filename in bias.DATA_MAP:
        dataset = bias.DATA_MAP[filename]
        attr_dist[filename] = dataset["distribution"]
    await SIO.emit("attribute_distribution", attr_dist, room=sid)


@SIO.event
def disconnect(sid):
    if sid in CLIENT_SOCKET_ID_PARTICIPANT_MAPPING:
        pid = CLIENT_SOCKET_ID_PARTICIPANT_MAPPING[sid]
        if pid in CLIENTS:
            CLIENTS[pid]["disconnected_at"] = bias_util.get_current_time()
            print(f"Disconnected: Participant ID: {pid} | Socket ID: {sid}")


@SIO.event
async def on_session_end_page_level_logs(sid, payload):
    pid = payload["participantId"]
    if pid in CLIENTS and "data" in payload:
        dirname = f"output/{CLIENTS[pid]['app_type']}/{pid}"
        Path(dirname).mkdir(exist_ok=True) 
        filename = f"output/{CLIENTS[pid]['app_type']}/{pid}/session_end_page_logs_{pid}_{bias_util.get_current_time()}.tsv"
        df_to_save = pd.DataFrame(payload["data"])

        # persist to disk
        df_to_save.transpose().to_csv(filename, sep="\t")

        print(f"Saved session logs to file: {filename}")


@SIO.event
async def on_save_logs(sid, data):
    if sid in CLIENT_SOCKET_ID_PARTICIPANT_MAPPING:
        pid = CLIENT_SOCKET_ID_PARTICIPANT_MAPPING[sid]
        if pid in CLIENTS:
            dirname = f"output/{CLIENTS[pid]['app_type']}/{pid}"
            Path(dirname).mkdir(exist_ok=True)
            filename = f"output/{CLIENTS[pid]['app_type']}/{pid}/logs_{pid}_{bias_util.get_current_time()}.tsv"
            df_to_save = pd.DataFrame(CLIENTS[pid]["response_list"])

            # persist to disk
            df_to_save.to_csv(filename, sep="\t")

            print(f"Saved logs to file: {filename}")

@SIO.event
async def on_interaction(sid, data):
    app_mode = data["appMode"]  # The dataset that is being used, e.g. cars.csv
    app_type = data["appType"]  # CONTROL / AWARENESS / ADMIN
    app_level = data["appLevel"]  # live / practice
    pid = data["participantId"]
    interaction_type = data["interactionType"] # Interaction type - eg. hover, click

    # Let these get updated everytime an interaction occurs, to handle the
    #   worst case scenario of random restart of the server.
    CLIENT_SOCKET_ID_PARTICIPANT_MAPPING[sid] = pid
    CLIENT_PARTICIPANT_ID_SOCKET_ID_MAPPING[pid] = sid

    if pid not in CLIENTS:
        # new participant => establish data mapping for them!
        CLIENTS[pid] = {}
        CLIENTS[pid]["id"] = sid
        CLIENTS[pid]["participant_id"] = pid
        CLIENTS[pid]["app_mode"] = app_mode
        CLIENTS[pid]["app_type"] = app_type
        CLIENTS[pid]["app_level"] = app_level
        CLIENTS[pid]["connected_at"] = bias_util.get_current_time()
        CLIENTS[pid]["bias_logs"] = []
        CLIENTS[pid]["response_list"] = []

    if app_mode != CLIENTS[pid]["app_mode"] or app_level != CLIENTS[pid]["app_level"]:
        # datasets have been switched => reset the logs array!
        # OR
        # app_level (e.g. practice > live) is changed but same dataset is in use => reset the logs array!
        CLIENTS[pid]["app_mode"] = app_mode
        CLIENTS[pid]["app_level"] = app_level
        CLIENTS[pid]["bias_logs"] = []
        CLIENTS[pid]["response_list"] = []

    # record response to interaction
    response = {}
    response["sid"] = sid
    response["participant_id"] = pid
    response["app_mode"] = app_mode
    response["app_type"] = app_type
    response["app_level"] = app_level
    response["processed_at"] = bias_util.get_current_time()
    response["interaction_type"] = interaction_type
    response["input_data"] = data

    # check whether to compute bias metrics or not
    if interaction_type in COMPUTE_BIAS_FOR_TYPES:
        CLIENTS[pid]["bias_logs"].append(data)
        metrics = bias.compute_metrics(app_mode, CLIENTS[pid]["bias_logs"])
        response["output_data"] = metrics
    else:
        response["output_data"] = None

    # save response
    CLIENTS[pid]["response_list"].append(response)

    await SIO.emit("log", response)  # send this to all
    await SIO.emit("interaction_response", response, room=sid)


if __name__ == "__main__":
    bias.precompute_distributions()
    port = int(os.environ.get("PORT", 3000))
    web.run_app(APP, port=port)
