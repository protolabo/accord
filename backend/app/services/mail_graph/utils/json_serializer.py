import json
import copy
import numpy as np


def serialize_node(node):
    """
    Convert a node to a JSON-serializable format.

    Args:
        node: Node dictionary to serialize

    Returns:
        JSON-serializable version of the node
    """
    node_copy = copy.deepcopy(node)

    # Convert any non-serializable values
    for key, value in node_copy.items():
        if isinstance(value, (set, frozenset)):
            node_copy[key] = list(value)
        elif isinstance(value, np.ndarray):
            node_copy[key] = value.tolist()

    return node_copy


def save_component_to_json(data, filepath, serialize=True):
    """
    Save a component (nodes or relations) to a JSON file.

    Args:
        data: Data to save
        filepath: Path where to save the file
        serialize: Whether to serialize the data first
    """
    if serialize:
        if isinstance(data, dict):
            serialized_data = {k: serialize_node(v) for k, v in data.items()}
        else:
            serialized_data = [serialize_node(item) for item in data]
    else:
        serialized_data = data

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(serialized_data, f, ensure_ascii=False)