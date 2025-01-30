from datetime import datetime
import os
import random
from flask import Flask, send_from_directory, send_file, request, jsonify
from flask_socketio import SocketIO
from mmdx.search import VectorDB
from mmdx.model import ClipModel
from mmdx.settings import (
    DATA_PATH,
    DB_PATH,
    DB_DELETE_EXISTING,
    DB_BATCH_LOAD,
    ACCESS_KEY,
    ENDPOINT_URL,
    SECRET_KEY,
    DATA_SOURCE,
    LOAD_DATA,
)
from mmdx.s3_client import S3Client
# from LTS import main
from io import BytesIO
import json
import random
import time
from LTS.main import initialize_LTS
from LTS.lts_processing import LTS

app = Flask(__name__)
# CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

stop_task = False
# Path for our main Svelte app. All routes in the app must be added
# here to allow refreshing to work correctly.
@app.route("/")
@app.route("/search/random")
@app.route("/search/image")
@app.route("/labels")
@app.route("/bootstrap")
def base():
    return send_from_directory("client/dist/", "index.html")

@socketio.on('my event')
def test_message(message):
    socketio.emit('my response', {'data': f'{random.random()}' })

@socketio.on('start training')
def test_message(message):
    global stop_task
    stop_task = False
    socketio.start_background_task(target=train_model, message=message)
    socketio.emit('my response', {'message': 'Training started!'})

# @socketio.on('connect')
# def test_connect():
#     emit('my response', {'data': 'Connected'})

@socketio.on('stop_training')
def test_disconnect(message):
    global stop_task
    stop_task = True
    os.environ['CSV_PATH'] = f"{message['projectId']}/current_sample_training.csv"
    global db
    db = create_db_for_data_path(S3_Client)
    print('Client disconnected')


# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def assets(path):
    return send_from_directory("client/dist/", path)


@app.route("/images/<path:path>")
def images(path):
    if DATA_SOURCE.upper() == "S3":
        image_data = S3_Client.get_obj(DATA_PATH, path)
        image_buffer = BytesIO(image_data.read())
        return send_file(
            image_buffer,
            as_attachment=False,
            download_name=path,
        )
    else:
        return send_from_directory(DATA_PATH, path)


@app.route("/api/v1/random")
def random_search():
    limit: int = request.args.get("limit", 12, type=int)
    hits = db.random_search(limit=limit)
    return {"total": len(hits.index), "hits": hits.to_dict("records")}


@app.route("/api/v1/keyword_search")
def keyword_search():
    query: str = request.args.get("q")
    exclude_labeled: bool = request.args.get("exclude_labeled", "false") == "true"
    limit: int = request.args.get("limit", 12, type=int)
    hits = db.search_by_text(query_string=query, limit=limit, exclude_labeled=exclude_labeled)
    return {"total": len(hits.index), "hits": hits.to_dict("records")}


@app.route("/api/v1/image_search")
def image_search():
    query: str = request.args.get("q")
    exclude_labeled: bool = request.args.get("exclude_labeled", "false") == "true"
    limit: int = request.args.get("limit", 12, type=int)
    hits = db.search_by_image_path(
        image_path=query, limit=limit, S3_Client=S3_Client, exclude_labeled=exclude_labeled
    )
    return {"total": len(hits.index), "hits": hits.to_dict("records")}


@app.route("/api/v1/seller_search")
def seller_search():
    query: str = request.args.get("q")
    exclude_labeled: bool = request.args.get("exclude_labeled", "false") == "true"
    limit: int = request.args.get("limit", 12, type=int)
    hits = db.search_by_seller(query_string=query, limit=limit, exclude_labeled=exclude_labeled)
    return {"total": len(hits.index), "hits": hits.to_dict("records")}

@app.route("/api/v1/labeled")
def labeled_search():
    limit: int = request.args.get("limit", 12, type=int)
    hits = db.search_labeled_data(limit=limit)
    return {"total": len(hits.index), "hits": hits.to_dict("records")}

@app.route("/api/v1/add_label")
def add_label():
    image_path: str = request.args.get("image_path", None, type=str)
    label: str = request.args.get("label", None, type=str)
    table: str = request.args.get("table", None, type=str)
    db.add_label(image_path=image_path, label=label, table=table)
    return {"success": True}


@app.route("/api/v1/remove_label")
def remove_label():
    image_path: str = request.args.get("image_path", None, type=str)
    label: str = request.args.get("label", None, type=str)
    table: str = request.args.get("table", None, type=str)
    db.remove_label(image_path=image_path, label=label, table=table)
    return {"success": True}


@app.route("/api/v1/labels")
def labels():
    table: str = request.args.get("table", None, type=str)
    labels = db.get_labels(table)
    return {"labels": labels}


@app.route("/api/v1/label_counts")
def label_counts():
    counts = db.get_label_counts()
    print(counts)
    return {"counts": counts}


@app.route("/api/v1/download/binary_labeled_data")
def download_binary_labeled_data():
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"labeled_data_{current_time}.zip"
    output_zip_file = db.create_zip_labeled_binary_data(
        output_dir=os.path.join(DB_PATH, "downloads"),
        filename=filename
    )
    print("Created zip file: ", output_zip_file)
    return send_file(output_zip_file, as_attachment=True)

@app.route("/api/v1/load/start_lts_generation", methods=['POST'])
def start_lts_generation():
    try:
        data = request.get_json()
        # Extract the prompt text
        args = data.get('argsDict')
        project_id = data.get('ProjectId')
        print(project_id)

        if not args:
            return {'message': 'No prompt provided'}
        if not os.path.exists(project_id):
            os.makedirs(project_id)
        with open(f"{project_id}/config_file.json", "w") as file:
            json.dump(args, file)
        return {'message': 'config create successfully'}
        # main(sampler, data, sample_size, filter_label, trainer, labeler, filename, balance, metric, baseline, labeling, retrain, idx, id)

    except Exception as e:
        return {'message': f'Config file not create {e}'}

# def train_model(message):
#     project_id = message["data"]
#     args, sampler, data, trainer, labeler = initialize_LTS(project_id)
#     budget = args.get("budget")
#     budget_value = int(args.get("bugetValue"))
#     training_results = []
#     if budget == "trainingSize":
#         loops = int(budget_value/args.get("sample_size"))
#         for idx in range(loops):
#             if stop_task:
#                 print("Training stopped!")
#                 break
#             result =  LTS(sampler, data, args.get("sample_size"), True, trainer, labeler, "filename", True, args.get("metric"), args.get("baseline"), args.get("labeling"), idx, project_id)
#             result = {
#                 "step": idx,
#                 "precision": result["eval_precision"],
#                 "recall": result["eval_recall"],
#                 "f1_score": result["eval_f1"],
#                 "accuracy": result["eval_accuracy"]
#             }
#             training_results.append(result)
#             socketio.emit('my response', result)
#             time.sleep(120)

#     elif budget=="metric":
#         generate = True
#         idx = 0
#         while generate:
#             if stop_task:
#                 print("Training stopped!")
#                 break
#             result = LTS(sampler, data, args.get("sample_size"), True, trainer, labeler, "filename", True, args.get("metric"), args.get("baseline"), args.get("labeling"), idx, project_id)
#             if result[f'eval_{args.get("metric")}'] >= budget_value:
#                 generate = False
#             idx+=1
#             result = {
#                 "step": idx,
#                 "precision": result["eval_precision"],
#                 "recall": result["eval_recall"],
#                 "f1_score": result["eval_f1"],
#                 "accuracy": result["eval_accuracy"]
#             }

#             training_results.append(result)

#             # Emit the training result after each step
#             socketio.emit('my response', result)
#             time.sleep(120)

#     if not stop_task:
#         socketio.emit('my response', {'message': 'Training complete!'})
#     else:
#         socketio.emit('my response', {'message': 'Training stopped by user'})
    # Emit a final message when training is complete

def train_model(message):
    print(message)
    projectId = message.get("projectId")

    if message.get("labeling") == "file":
        db.create_labeled_data(projectId)

    for idx in range(0, 4):
        if stop_task:
            print("Training stopped!")
            break
        # Fake evaluation metrics (you can replace with actual metrics from your model)
        precision = random.uniform(0.6, 1.0)  # Fake precision value between 0.6 and 1.0
        recall = random.uniform(0.6, 1.0)     # Fake recall value between 0.6 and 1.0
        f1_score = 2 * (precision * recall) / (precision + recall)  # Fake f1_score formula
        accuracy = random.uniform(0.6, 1.0)  # Fake accuracy value between 0.6 and 1.0

        result = {
            "step": idx,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1_score, 4),
            "accuracy": round(accuracy, 4)
        }

        # Emit the result via SocketIO
        socketio.emit('my response', result)

        # Wait for 10 seconds before the next emission
        time.sleep(10)

    if not stop_task:
        socketio.emit('my response', {'message': 'Training complete!'})
    else:
        socketio.emit('my response', {'message': 'Training stopped by user'})
    # Emit a final message when training is complete
    socketio.emit('my response', {'message': 'Training complete!'})

@app.route("/api/v1/load/csv_data", methods=['POST'])
def create_database():
    # try:
    if 'file' not in request.files:
        return {'error': 'No file part'}

    file = request.files['file']

    if file.filename == '':
        raise ValueError('No selected file')

    project_id = request.form.get('projectId')
    if project_id =='':
        return {'error': 'Please add a project ID'}
    # Get the CSV file from the form data

    filename = file.filename
    # filepath = os.path.join(project_id, filename)

    project_dir = os.path.join(project_id)
    print(project_dir)
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    file_path = os.path.join(project_dir, filename)

    # file.save(filepath)
    file.save(file_path)

    return {'message': 'CSV data received and processed successfully'}


def create_db_for_data_path(S3_Client):
    data_path = DATA_PATH
    db_path = DB_PATH

    if DATA_SOURCE.upper() == "S3":
        data_path_msg = f" - Data Bucket: {data_path}"
    else:
        S3_Client = None
        data_path_msg = f" - Raw data path: {os.path.abspath(data_path)}"

    print("Loading embedding model...")
    model = ClipModel()

    print(f"Loading vector database:")
    print(f" - DB path: {os.path.abspath(db_path)}")
    print(data_path_msg)
    print(f" - Delete existing?: {DB_DELETE_EXISTING}")
    print(f" - Batch load?: {DB_BATCH_LOAD}")
    vectordb = VectorDB.from_data_path(
        data_path,
        db_path,
        S3_Client,
        model,
        delete_existing=DB_DELETE_EXISTING,
        batch_load=DB_BATCH_LOAD,
    )
    print("Finished DB initialization.")
    return vectordb


if DATA_SOURCE.upper() == "S3":
    S3_Client = S3Client(
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        endpoint_url=ENDPOINT_URL,
    )
else:
    S3_Client=None

if LOAD_DATA:
    db: VectorDB = None
else:
    db: VectorDB = create_db_for_data_path(S3_Client)

if __name__ == "__main__":
    if os.environ.get("ENV") == "prod":
        # app.run(debug=False, host="0.0.0.0")
        socketio.run(app, debug=False, host="0.0.0.0")
    else:
        socketio.run(app, debug=True, host="127.0.0.1")
