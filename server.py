import threading
from utils.runpod import fetch_minimum_bid_price, get_pods, rent_pod
import time
from typing import Union
import os
from utils.redis_helper import get_queue_length
from tasks import train_dreambooth, task_done_handler
from celery.result import AsyncResult
from flask import jsonify, request
from celery import Celery, Task, chain
from flask import Flask
from dotenv import load_dotenv
load_dotenv()


def get_active_tasks(app: Flask) -> int:
    # Get the celery instance from the app
    celery = app.extensions["celery"]
    # Inspect all nodes.
    i = celery.control.inspect()
    # Get the active tasks
    active_tasks = i.active()
    # If there are active tasks, calculate the total, otherwise return 0
    if active_tasks:
        tasks_in_progress = sum(len(v) for v in active_tasks.values())
    else:
        tasks_in_progress = 0

    return tasks_in_progress


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.conf.update(
        broker_url=os.getenv("CELERY_BROKER_URL"),
        result_backend=os.getenv("CELERY_RESULT_BACKEND"),
        task_ignore_result=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_track_started=True,
    )
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url=os.getenv("CELERY_BROKER_URL"),
            result_backend=os.getenv("CELERY_RESULT_BACKEND"),
            task_ignore_result=True,
        ),
    )
    app.config.from_prefixed_env()
    celery_init_app(app)
    return app


app = create_app()


@app.post("/run-dreambooth")
def start_add() -> dict[str, object]:
    user_id = request.form.get("user_id", type=int)
    model_id = request.form.get("model_id", type=int)
    pods = get_pods()
    active_tasks = get_active_tasks(app)
    extra_pods = len(pods) - active_tasks
    queue_length = get_queue_length() + 1
    print(queue_length - extra_pods)
    print("Active Tasks:", active_tasks)
    print("Extra Pods:", extra_pods)
    print("Queue Length:", queue_length)
    for i in range(0, queue_length - extra_pods):
        min_bid_price = fetch_minimum_bid_price("NVIDIA GeForce RTX 4090")
        rent_pod("NVIDIA GeForce RTX 4090", min_bid_price+0.01)
    result = train_dreambooth.delay(user_id, model_id)
    return {"result_id": result.id}


@app.get("/status/<id>")
def task_result(id: str) -> dict[str, object]:
    result = AsyncResult(id)
    response = {
        "job_id": result.task_id,
        "state": result.state,
        "meta": result.info
    }
    if result.ready():
        if isinstance(result.result, Exception):
            # In case of an exception, return its string representation
            response["result"] = str(result.result)
        else:
            response["result"] = result.result
    return response


@app.get("/queue-length")
def queue_length() -> dict[str, Union[str, int]]:
    try:
        length = get_queue_length()
        return {"queue_length": length}
    except Exception as e:
        return {"error": str(e)}


@app.route('/tasks-in-progress', methods=['GET'])
def tasks_in_progress():
    active_tasks = get_active_tasks(app)
    return jsonify({"tasks_in_progress": active_tasks})
