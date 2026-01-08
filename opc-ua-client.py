import asyncio
import joblib
import os
import torch

import numpy as np

from asyncua import Client
from torch import nn


INPUT_VARIABLES = [
    "air_temperature",
    "attached_weight",
    "position_x",
    "position_y",
    "process_temperature",
    "speed",
    "speed_next",
]
ORCHESTRATION_VARIABLES = ["cycle", "process_step"]


# Map input variable names to feature column names
NAME_MAPPING = {
    "air_temperature": "Air temperature [K]",
    "attached_weight": "Attached Weight [mg]",
    "cycle": "cycle",
    "error_x": "error_x",
    "error_y": "error_y",
    "position_x": "Position x [mm]",
    "position_y": "Position y [mm]",
    "process_step": "Process step",
    "process_temperature": "Process temperature [K]",
    "speed": "Speed [mm/s]",
    "speed_next": "Speed next [mm/s]",
}


## >>> EXERCISE (PART 10/10): Stop datachange notification
DATACHANGE_NOTIFICATION = True
## <<<

## >>> EXERCISE (PART 1/10): Load your model (and optionally also the scaler)

## <<<


class SubHandler:
    """
    Subscription Handler. To receive events from server for a subscription.
    """

    def __init__(self, feature_names, correction_nodes):
        self.current_step = None
        self.feature_names = feature_names
        self.latest_values = {name: None for name in feature_names}
        self.node_to_feature = {}
        self.step_data = []
        self.correction_nodes = correction_nodes
        self.cycle = 0

    def datachange_notification(self, node, val, data):
        feature_name = self.node_to_feature.get(node, "Unknown")

        DATACHANGE_NOTIFICATION and print(
            f"Data change on {feature_name} (node {node}) - {val} at {data.monitored_item.Value.ServerTimestamp}"
        )

        if feature_name in self.feature_names:
            # Update latest values
            self.latest_values[feature_name] = val
        elif feature_name == "cycle":
            # Update cycle client-side
            print("Starting new cycle, resetting state.", flush=True)
            self.cycle = val
            self.latest_values = {name: None for name in self.feature_names}
        elif feature_name == "process_step":
            # Process step changed
            if self.current_step is not None:
                print(f"\nProcess step {self.current_step} completed.", flush=True)

            self.current_step = val

            if self.current_step == 2:
                if all(
                    self.latest_values.get(var) is not None for var in INPUT_VARIABLES
                ):
                    print("Computing correction values.", flush=True)
                    self._compute_and_write_corrections(
                        self.latest_values.copy(), self.cycle
                    )  # Pass a copy to avoid mutation issues during runtime
                else:
                    print(
                        "Warning: Not all input variables were collected before step change.",
                        flush=True,
                    )
                    print(
                        "Missing: ",
                        [
                            var
                            for var in self.feature_names
                            if self.latest_values.get(var) is None
                        ],
                        flush=True,
                    )
                    print("Skip correction computation.", flush=True)

    def _compute_and_write_corrections(self, latest_values, cycle):
        """Process step data and write corrections."""

        ## >>> EXERCISE (PART 9/10): Remove pass
        pass
        ## <<<

        print("\nProcessing step data...", flush=True)

        ## >>> EXERCISE (PART 6/10): Print latest_values

        ## <<<

        print("Calculating correction values using model...", flush=True)
        starttime = asyncio.get_event_loop().time()

        ## >>> EXERCISE (PART 7/10): Call predict_error to get corr_x and corr_y

        ## <<<

        endtime = asyncio.get_event_loop().time()
        print(f"Data processed in {endtime - starttime:.4f} seconds.")

        ## >>> EXERCISE (PART 8/10): Write correction values to OPC UA nodes. Also add a print-statement showing the values in console.

        # asyncio.create_task(self.correction_nodes['correction_x'].write_value(..))
        # asyncio.create_task(self.correction_nodes['correction_y'].write_value(..))
        # asyncio.create_task(self.correction_nodes['correction_cycle'].write_value(..))
        ## <<<


def predict_error(input_data):
    """Process collected data and predict correction values using the trained model."""
    ## >>> EXERCISE (PART 2/10): Provide a list of features used for your model in correct order
    # Expected feature order from the notebook - modify as needed (ordering, removal of entries), but do not change the names
    feature_cols = [
        "Air temperature [K]",
        "Attached Weight [mg]",
        "Position x [mm]",
        "Position y [mm]",
        "Process temperature [K]",
        "Speed [mm/s]",
        "Speed next [mm/s]",
    ]
    ## <<<

    # Extract features in the correct order
    features = []

    for col in feature_cols:
        # Find the corresponding input variable name
        input_key = [k for k, v in NAME_MAPPING.items() if v == col][0]
        features.append(input_data.get(input_key, 0.0))

    # Convert to numpy array
    X = np.array([features], dtype=np.float32)

    ## >>> EXERCISE (PART 3/10): Optional - Scale input data, if your model requires it

    ## <<<

    ## >>> EXERCISE (PART 4/10): Predict error_x and error_y using your model

    ## <<<

    ## >>> EXERCISE (PART 5/10): Use error_x and error_y to provide correction values corr_x and corr_y
    corr_x = 0.0
    corr_y = 0.0
    ## <<<

    return corr_x, corr_y


async def main():
    url = "opc.tcp://localhost:4840"
    client = None

    while client is None:
        try:
            client = Client(url=url)
            await client.connect()
            print("Client connected to OPC UA server.")
        except Exception as e:
            client = None
            print(f"Connection failed: {e}. Retrying in 2 seconds...")
            await asyncio.sleep(2)
            continue

        # Browse all nodes under the Objects folder to get all possible node ids
        root = client.get_root_node()
        objects = await root.get_child(["0:Objects", "2:plcSimulator"])
        children = await objects.get_children()

        nodes = {}

        for child in children:
            display_name = await child.read_display_name()
            node_id = child.nodeid.to_string()
            nodes[display_name.Text] = client.get_node(node_id)

        # Prepare correction nodes for the handler
        correction_nodes = {
            "correction_x": nodes["correction_x"],
            "correction_y": nodes["correction_y"],
            "correction_cycle": nodes["correction_cycle"],
        }

        handler = SubHandler(INPUT_VARIABLES, correction_nodes)
        frequency = 10  # ms

        handles = []

        for feature_name, node in nodes.items():
            if feature_name in INPUT_VARIABLES + ORCHESTRATION_VARIABLES:
                subscription = await client.create_subscription(frequency, handler)
                handle = await subscription.subscribe_data_change(node)
                handles.append(handle)
                handler.node_to_feature[node] = feature_name

        print("Subscribed to nodes. Listening for data changes (Ctrl+C to exit)...")
        try:
            while True:
                await asyncio.sleep(0.001)
        except KeyboardInterrupt:
            print("Interrupted by user.")
        finally:
            await subscription.delete()
            print("Subscription deleted.")


if __name__ == "__main__":
    asyncio.run(main())
