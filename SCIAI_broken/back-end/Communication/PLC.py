from pycomm3 import LogixDriver


class PLC:
    """
    Represents a PLC
    """
    def __init__(self, ip_address):
        """
        Initializes an instance of PLC with the given IP address
        :param ip: IP Address of the PLC
        """
        self.ip_address = ip_address
        self.driver = None

    def connect(self):
        """
        Establishes a connection to the PLC
        :return: True on success, False on failure
        """
        try:
            self.driver = LogixDriver(self.ip_address)
            self.driver.open()
            print(f"PLC: Connected to {self.ip_address}")
            return True
        except Exception as e:
            print(f"PLC: Failed to connect to {self.ip_address}")
            return False

    def read_tag(self, tag_name: str):
        """
        Reads a tag from the PLC
        :param tag_name: Name of the tag to read
        :return: Value of the tag, None upon failure
        """
        if self.driver is None:
            print(f"PLC: Not connected to {self.ip_address} to read.")
            return None

        try:
            response = self.driver.read(tag_name)
            if response is None:
                print(f"PLC: Read failed for tag {tag_name} at IP {self.ip_address}")
                return None
            return response.value
        except Exception as e:
            print(f"PLC: Exception during read of {self.ip_address}: {e}")
            return None

    def write_tag(self, tag_name: str, value):
        """
        Writes a value to PLC tag
        :param tag_name: Name of the tag to write
        :param value: Value to write
        :return: True on success, False on failure
        """
        if self.driver is None:
            print(f"PLC: Not connected to {self.ip_address} to write.")
            return None

        try:
            response = self.driver.write(tag_name, value)
            if response:
                return True
            print(f"PLC: Write failed for tag {tag_name} at IP {self.ip_address}")
            return False
        except Exception as e:
            print(f"PLC: Exception during write of {self.ip_address}: {e}")
            return False

    def close(self):
        """
        Closes the connection to the PLC
        """
        if self.driver:
            self.driver.close()
            print(f"PLC: Connection to {self.ip_address} closed.")

