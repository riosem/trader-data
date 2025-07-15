import os

from task.train import train_new_model
from task.predict import generate_prediction

provider = os.getenv("PROVIDER")
product_id = os.getenv("PRODUCT_ID")
correlation_id = os.getenv("CORRELATION_ID")
action = os.getenv("ACTION")


if __name__ == "__main__":
    if action == "train":
        train_new_model(provider, product_id, correlation_id)
    elif action == "predict":
        generate_prediction(provider, product_id, correlation_id)
