from . import config


def load_ml_models(model_path: str, config: config.Config) -> dict:
    """
    Load the model from the given path and return the model dictionary.
    """
    # Load the model
    model = {}
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    # Check if the model is valid
    if not isinstance(model, dict):
        raise ValueError("Model is not a valid dictionary.")

    # Check if the model contains the required keys
    required_keys = ["features", "matches", "retrieval"]
    for key in required_keys:
        if key not in model:
            raise ValueError(f"Model does not contain the required key: {key}")

    return model