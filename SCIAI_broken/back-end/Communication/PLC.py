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
            # Ensure we don't leave a half-initialized driver that will later raise session errors
            print(f"PLC: Failed to connect to {self.ip_address}: {e}")
            self.driver = None
            return False

    def read_tag(self, tag_name: str):
        """
        Reads a tag from the PLC
        :param tag_name: Name of the tag to read
        :return: Value of the tag, None upon failure
        """
        if self.driver is None:
            print(f"PLC: Not connected to {self.ip_address} to read. Attempting to connect.")
            if not self.connect():
                print(f"PLC: Connect failed; cannot read {tag_name} at {self.ip_address}")
                return None

        try:
            response = self.driver.read(tag_name)
            if response is None:
                print(f"PLC: Read failed for tag {tag_name} at IP {self.ip_address}")
                return None
            return response.value
        except Exception as e:
            msg = str(e).lower()
            # Try to recover from a lost/unregistered session by re-opening once
            if "session must be registered" in msg or "forward open" in msg:
                print(f"PLC: Session error when reading {self.ip_address}: {e}. Attempting to reopen connection.")
                try:
                    # Attempt to reopen or recreate driver
                    if self.driver is None:
                        self.driver = LogixDriver(self.ip_address)
                    self.driver.open()
                    response = self.driver.read(tag_name)
                    if response is None:
                        print(f"PLC: Read retry failed for tag {tag_name} at IP {self.ip_address}")
                        return None
                    return response.value
                except Exception as e2:
                    print(f"PLC: Read retry failed for {self.ip_address}: {e2}")
                    # Reset driver to force explicit reconnect next time
                    try:
                        self.driver.close()
                    except Exception:
                        pass
                    self.driver = None
                    return None
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
            print(f"PLC: Not connected to {self.ip_address} to write. Attempting to connect.")
            if not self.connect():
                print(f"PLC: Connect failed; cannot write to {tag_name} at {self.ip_address}")
                return None

        try:
            response = self.driver.write(tag_name, value)
            if response:
                return True
            print(f"PLC: Write failed for tag {tag_name} at IP {self.ip_address}: {response.error}")
            return False
        except Exception as e:
            msg = str(e).lower()
            # Try to recover from a lost/unregistered session by re-opening once
            if "session must be registered" in msg or "forward open" in msg:
                print(f"PLC: Session error when writing to {self.ip_address}: {e}. Attempting to reopen connection.")
                try:
                    if self.driver is None:
                        self.driver = LogixDriver(self.ip_address)
                    self.driver.open()
                    response = self.driver.write(tag_name, value)
                    if response:
                        return True
                    print(f"PLC: Write retry failed for tag {tag_name} at IP {self.ip_address}: {getattr(response, 'error', None)}")
                    return False
                except Exception as e2:
                    print(f"PLC: Write retry failed for {self.ip_address}: {e2}")
                    try:
                        self.driver.close()
                    except Exception:
                        pass
                    self.driver = None
                    return False
            print(f"PLC: Exception during write of {self.ip_address}: {e}")
            return False

    def write_tags(self, *tag_value_pairs):
        """
        Writes multiple tags in a single CIP message (one network round-trip).
        :param tag_value_pairs: Tuples of (tag_name, value)
        :return: True on success, False on failure
        """
        if self.driver is None:
            print(f"PLC: Not connected to {self.ip_address} to write. Attempting to connect.")
            if not self.connect():
                print(f"PLC: Connect failed; cannot write to {self.ip_address}")
                return False

        try:
            responses = self.driver.write(*tag_value_pairs)
            if not isinstance(responses, list):
                responses = [responses]
            if all(r for r in responses):
                return True
            for r in responses:
                if not r:
                    print(f"PLC: Write failed for tag {r.tag} at IP {self.ip_address}: {r.error}")
            return False
        except Exception as e:
            msg = str(e).lower()
            if "session must be registered" in msg or "forward open" in msg:
                print(f"PLC: Session error when writing to {self.ip_address}: {e}. Attempting to reopen connection.")
                try:
                    if self.driver is None:
                        self.driver = LogixDriver(self.ip_address)
                    self.driver.open()
                    responses = self.driver.write(*tag_value_pairs)
                    if not isinstance(responses, list):
                        responses = [responses]
                    if all(r for r in responses):
                        return True
                    return False
                except Exception as e2:
                    print(f"PLC: Write retry failed for {self.ip_address}: {e2}")
                    try:
                        self.driver.close()
                    except Exception:
                        pass
                    self.driver = None
                    return False
            print(f"PLC: Exception during write of {self.ip_address}: {e}")
            return False

    def close(self):
        """
        Closes the connection to the PLC
        """
        if self.driver:
            self.driver.close()
            print(f"PLC: Connection to {self.ip_address} closed.")

