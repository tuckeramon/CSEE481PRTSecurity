# api.py
"""
Frontend API module - Direct database access for cart commands

CHANGE: Removed HTTP-based communication to backend Server.py
OLD: Used requests.post() to send commands to localhost:2650
NEW: Writes directly to database tables that backend polls

Architecture:
- send_cart_to_station() -> Updates PRTCarts.destination directly
- remove_cart() -> Inserts into PRTRemoveCart table

Backend (main.py) reads from these tables:
- PRTCarts: Read when PLC requests routing info for a cart
- PRTRemoveCart: Polled for new removal commands
"""

from models.db import (
    update_cart_destination,
    insert_remove_cart_command,
    log_event
)


def send_cart_to_station(cart_id, station_id):
    """
    Update cart destination directly in database.
    Backend will read this when PLC requests routing info.

    :param cart_id: Cart barcode (e.g., "0001")
    :param station_id: Station name (e.g., "Station_1")
    """
    station_map = {
        "Station_1": 1,
        "Station_2": 2,
        "Station_3": 3,
        "Station_4": 4
    }
    destination = station_map.get(station_id)

    if destination is None:
        print(f"Invalid station: {station_id}")
        return False

    # Update destination in PRTCarts table
    success = update_cart_destination(cart_id, destination)

    # Log the action to cart_logs for activity tracking
    if success:
        log_event(cart_id, station_id, "Destination Updated", "Command")
        print(f"Cart {cart_id} destination set to {station_id}")
    else:
        log_event(cart_id, station_id, "Update Failed", "Error")
        print(f"Failed to update cart {cart_id} destination")

    return success


def remove_cart(cart_id, area):
    """
    Insert cart removal command into database.
    Backend will poll PRTRemoveCart and process the command.

    :param cart_id: Cart barcode (e.g., "0001")
    :param area: Removal area number (5-9)
    """
    # Insert removal command into PRTRemoveCart table
    success = insert_remove_cart_command(cart_id, area)

    # Log the action to cart_logs for activity tracking
    if success:
        log_event(cart_id, f"Remove_Area_{area}", "Removal Requested", "Command")
        print(f"Cart {cart_id} removal requested to area {area}")
    else:
        log_event(cart_id, f"Remove_Area_{area}", "Removal Failed", "Error")
        print(f"Failed to request removal for cart {cart_id}")

    return success
