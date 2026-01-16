import pandas as pd
import os
from datetime import datetime
from DataCollection.FileManager import FileManager


class DataLogger:
    """
    Log data using pandas and support flexible columns and data-types via **kwargs
    """
    def __init__(self, log_dir: str, plot_dir: str):
        """
        Initializes an instance of DataLogger
        :param log_dir: Directory to store log files
        :param plot_dir: Directory to store plots
        """
        self.log_manager = FileManager(log_dir)
        self.plot_dir = plot_dir
        os.makedirs(self.plot_dir, exist_ok=True)
        self.data = pd.DataFrame()

    def log_data(self, **kwargs):
        """
        Logs data dynamically based on provided keyword arguments
        :param kwargs: Key-Value pairs of data to log
        """
        new_entry = pd.DataFrame([kwargs])  # Convert kwargs to single-row DataFrame
        self.data = pd.concat([self.data, new_entry], ignore_index=True)

    def save_log(self, file_name: str):
        """
        Saves logged data to a CSV file with the given name and creation time
        File named as {file_name}_Y-M-D-H-M-S.csv
        :param file_name: Name of log file
        """
        current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        file_path = self.log_manager.save_csv(self.data, f"{file_name}_{current_time}.csv")
        print(f"DataLogger: Log saved to {file_path}")

    def get_dataframe(self):
        """
        Returns logged data as a pandas DataFrame
        :return: Pandas DataFrame
        """
        return self.data

    def end_collection(self, file_name: str):
        """
        Saves self.data to file_name in CSV format
        Plots average trip time and average wait time
        :param file_name: Name of log file
        """
        self.save_log(file_name)

        # Analysis & Plotting






