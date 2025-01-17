import json
from collections import deque
import requests
import json
import copy
from collections import deque
import time
from urllib.parse import urlparse, parse_qs
import itertools
from copy import deepcopy

from flask import Blueprint, jsonify, request, redirect, url_for
from routes.auth import get_access_token

fields = Blueprint('customfields', __name__)

customfield_url = "https://app.clio.com/api/v4/custom_fields.json"
customfields_output_file = "customfields.json"
customfield_payload = {
            "limit": 200, #max
            "order": "display_order(asc)",
            "parent_type": "matter",
            "fields": "id,name,display_order,deleted"
        }
    
customfield_set_url = "https://app.clio.com/api/v4/custom_field_sets.json"
customfield_set_payload = {
            "limit": 200, #max
            "order": "name(asc)",
            "parent_type": "matter",
            "fields": "id,name,custom_fields{id,etag}"
        }
customfield_set_output_file = "customfield_sets.json"

_items = None
_item_sets = None
_last_cache_update = 0
_change_history = [] 

CACHE_EXPIRATION_SECONDS = 60

def is_cache_expired():
    """
    Check if the cache has expired based on the expiration timeframe.
    """
    return (time.time() - _last_cache_update) > CACHE_EXPIRATION_SECONDS

def get_items():
    return _items

def get_item_sets():
    return _item_sets

def set_items(items):
    global _items
    _items = items

def set_item_sets(item_sets):
    global _item_sets
    _item_sets = item_sets

def get_change_history():
    return _change_history

def set_change_history(change_history):
    global _change_history
    _change_history = change_history
    
def load_data_from_json(items_file_path, item_sets_file_path):
    global items, item_sets

    # Load JSON data from files
    with open(items_file_path, 'r') as items_file:
        raw_items = json.load(items_file)

    with open(item_sets_file_path, 'r') as item_sets_file:
        raw_item_sets = json.load(item_sets_file)
    
    # Process items
    items = [
        {
            "id": item["id"],
            "label": item["name"],
            "starting_position": item["display_order"],
            "current_position": item["display_order"],
            "history": deque([item["display_order"]])  # Initialize history with starting position
        }
        for item in raw_items
    ]

    # Process item sets
    item_sets = [
        {
            "id": item_set["id"],
            "label": item_set["name"],
            "items": [field["id"] for field in item_set.get("custom_fields", [])]
        }
        for item_set in raw_item_sets
    ]

def load_data_from_api(access_token, output_items_file_path, output_item_sets_file_path):
    global _items, _item_sets, _last_cache_update
    print("load_data_from_api called")
    
    # Load data from API
    raw_items = get_all_customfields(customfield_url, access_token, customfield_payload, output_items_file_path)
    raw_item_sets = get_all_customfield_sets(customfield_set_url, access_token, customfield_set_payload, output_item_sets_file_path)
    
    # Process items
    _items = [
        {
            "id": item["id"],
            "label": item["name"],
            "starting_position": item["display_order"],
            "current_position": item["display_order"],
            "deleted": item["deleted"],
            "history": list([item["display_order"]]) 
        }
        for item in raw_items
    ]

    _item_sets = [
        {
            "id": item_set["id"],
            "label": item_set["name"],
            "items": [field["id"] for field in item_set.get("custom_fields", [])]
        }
        for item_set in raw_item_sets
    ]
    _last_cache_update = time.time()

def get_all_customfields(api_url: str, token: str, initial_payload: dict, output_file: str):
    """
    Fetches all paginated results from the Clio API and saves the combined results to a JSON file.

    :param api_url: URL of the API endpoint.
    :param token: Bearer token for API authentication.
    :param initial_payload: The initial payload to send with the request.
    :param output_file: File path to save the combined JSON data.
    """
    all_data = []  # To store all results
    payload = initial_payload.copy()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    next_page_url = None

    while True:
        # Make the request
        print("Getting fields with API Request")
        response = requests.get(api_url, params=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} with message: {response.text}")
            break

        response_json = response.json()
        all_data.extend(response_json.get('data', []))  # Append the data from the current page

        # Get the next_page_url from the response
        next_page_url = response_json.get('meta', {}).get('paging', {}).get('next')
        
        if not next_page_url:
            break  # Exit loop if no more pages
        
        # Parse the next_page_token from the URL
        parsed_url = urlparse(next_page_url)
        query_params = parse_qs(parsed_url.query)
        next_page_token = query_params.get('page_token', [None])[0]

        if next_page_token:
            # Add the page_token to the payload for the next request
            payload['page_token'] = next_page_token
        else:
            break  # Exit loop if page_token is missing

    # Save the combined data to a JSON file
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=4)
    print(f"Data saved to {output_file}")
    return all_data

def get_all_customfield_sets(api_url: str, token: str, initial_payload: dict, output_file: str):
    """
    Fetches all paginated results from the Clio API and saves the combined results to a JSON file.

    :param api_url: URL of the API endpoint.
    :param token: Bearer token for API authentication.
    :param initial_payload: The initial payload to send with the request.
    :param output_file: File path to save the combined JSON data.
    """
    all_data = []  # To store all results
    payload = initial_payload.copy()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    next_page_url = None

    while True:
        # Make the request
        print("Getting field sets with API Request")
        response = requests.get(api_url, params=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} with message: {response.text}")
            break

        response_json = response.json()
        all_data.extend(response_json.get('data', []))  # Append the data from the current page

        # Get the next_page_url from the response
        next_page_url = response_json.get('meta', {}).get('paging', {}).get('next')
        
        if not next_page_url:
            break  # Exit loop if no more pages
        
        # Parse the next_page_token from the URL
        parsed_url = urlparse(next_page_url)
        query_params = parse_qs(parsed_url.query)
        next_page_token = query_params.get('page_token', [None])[0]

        if next_page_token:
            # Add the page_token to the payload for the next request
            payload['page_token'] = next_page_token
        else:
            break  # Exit loop if page_token is missing

    # Save the combined data to a JSON file
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=4)
    print(f"Data saved to {output_file}")
    return all_data
  
def update_fields(id, display_order):
    print("Updating FIelds")
    """
    Sends a PATCH request to the specified API URL with a Bearer token and JSON payload.

    Args:
        api_url (str): The API endpoint URL.
        access_token (str): The Bearer token for authorization.
        **kwargs: Additional parameters to include in the JSON payload.

    Returns:
        dict: The response from the API, parsed as JSON.
    """
    access_token = get_access_token()
    # print(access_token)
    api_url = f'https://app.clio.com/api/v4/custom_fields/{id}.json'
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "data": {
            "display_order": display_order
        }
    }

    try:
        # print(payload)
        # print(headers)
        # print(api_url)
        response = requests.patch(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        print(response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print(e)
        return {"error": str(e)}

@fields.route('/load-fields', methods=['POST'])
def load_fields():
    access_token = get_access_token()
    
    if not access_token:
        # Redirect to an error page or show a flash message
        return redirect(url_for('templates.upload_token'))  # Redirect to a token upload page
    
    # Check if items and item_sets are already loaded
    if not get_items() or not get_item_sets():
        load_data_from_api(access_token, customfields_output_file, customfield_set_output_file)

    items = get_items()
    item_sets = get_item_sets()

    # Sort items by current position for display
    sorted_items = sorted(items, key=lambda x: x["current_position"])

    # Prepare item sets with ordered items based on current_position
    ordered_item_sets = []
    for item_set in item_sets:
        ordered_items = sorted(
            [item for item in items if item["id"] in item_set["items"]],
            key=lambda x: x["current_position"]
        )
        ordered_item_sets.append({"id": item_set["id"], "label": item_set["label"], "ordered_items": ordered_items})
    print(ordered_item_sets)
    return jsonify(items=sorted_items, item_sets=ordered_item_sets)

@fields.route('/update-order', methods=['POST'])
def update_order():
    items = get_items()
    change_history = get_change_history()

    data = request.json
    moving_ids = data.get("moving_ids", [])
    target_position = data.get("target_position", None)

    if not moving_ids or target_position is None:
        return jsonify({"success": False, "message": "Invalid input data."})

    change_history.append(copy.deepcopy(items))
    set_change_history(change_history)

    moving_items = [item for item in items if item["id"] in moving_ids]
    moving_items.sort(key=lambda x: x["current_position"])

    remaining_items = [item for item in items if item["id"] not in moving_ids]

    adjusted_target_position = target_position
    for item in moving_items:
        if item["current_position"] < target_position:
            adjusted_target_position -= 1

    new_items = []
    for idx, item in enumerate(remaining_items):
        if idx == adjusted_target_position:
            new_items.extend(moving_items)
        new_items.append(item)

    if adjusted_target_position >= len(remaining_items):
        new_items.extend(moving_items)

    for idx, item in enumerate(new_items):
        item["current_position"] = idx
        # item.setdefault("history", deque()).append(idx) 

        if item["id"] in moving_ids:
            print(f'Sending to API: {item["id"]}, {idx}')
            update_fields(item["id"], idx)

    set_items(new_items)
    return jsonify({"success": True, "message": "All changes have been applied successfully."})

# @fields.route('/revert-order', methods=['POST'])
# def revert_order():
#     items = get_items()
#     change_history = get_change_history()

#     if not change_history:
#         return jsonify({"success": False, "message": "No changes to revert."})

#     # Peek at the last snapshot without removing it
#     previous_state = change_history[-1]

#     # Sort both lists by ID to ensure alignment
#     sorted_previous_state = sorted(previous_state, key=lambda x: x["id"])
#     sorted_items = sorted(items, key=lambda x: x["id"])

#     # Calculate distances moved for each item
#     moved_items = [
#         {
#             "id": prev_item["id"],
#             "current_position": current_item["current_position"],
#             "previous_position": prev_item["current_position"],
#             "distance_moved": abs(current_item["current_position"] - prev_item["current_position"]),
#         }
#         for prev_item, current_item in zip(sorted_previous_state, sorted_items)
#         if prev_item["current_position"] != current_item["current_position"]
#     ]

#     print(f"Moved items: {moved_items}")

#     # Generate all permutations of moves
#     all_permutations = itertools.permutations(moved_items)

#     # Simulate each permutation and track the number of API calls
#     min_api_calls = float('inf')
#     best_sequence = None

#     for permutation in all_permutations:
#         simulated_state = deepcopy(sorted_items)
#         api_calls = 0

#         for move in permutation:
#             # Simulate the move
#             for item in simulated_state:
#                 if item["id"] == move["id"]:
#                     item["current_position"] = move["previous_position"]
#             api_calls += 1

#             # Adjust subsequent items based on API's automatic shifting
#             for other_move in permutation:
#                 for item in simulated_state:
#                     if item["id"] == other_move["id"]:
#                         other_move["current_position"] = item["current_position"]

#         # Track the permutation with the fewest API calls
#         if api_calls < min_api_calls:
#             min_api_calls = api_calls
#             best_sequence = permutation

#     print(f"Optimal sequence: {best_sequence}, API calls: {min_api_calls}")

#     # Execute the optimal sequence
#     reverted_items = []
#     for move in best_sequence:
#         print(f"Reverting item {move['id']} from {move['current_position']} to {move['previous_position']}")
#         update_fields(move["id"], move["previous_position"])
#         reverted_items.append(move["id"])

#     # Pop the last snapshot after processing
#     change_history.pop()
#     set_change_history(change_history)

#     # Update shared storage with the reverted state
#     set_items(previous_state)

#     return jsonify({
#         "success": True,
#         "message": "Changes have been reverted.",
#         "reverted_items": reverted_items,
#     })

# @fields.route('/reset-order', methods=['POST'])
# def reset_order():
#     items = get_items()

#     if not items:
#         return jsonify({"success": False, "message": "No items to reset."})

#     # Reset all items to their starting positions
#     for item in items:
#         item["current_position"] = item["starting_position"]
#         item.setdefault("history", deque()).append(item["starting_position"])  # Update history
#         # update_fields(item["id"], item["starting_position"])

#     # Sort items by their starting position
#     items.sort(key=lambda x: x["starting_position"])

#     set_items(items)
#     return jsonify({"success": True, "message": "All changes have been undone. Items have been reset to their starting positions."})

# @fields.route('/finalize', methods=['POST'])
# def finalize():
#     items = get_items()

#     # Placeholder for the external API call
#     def external_api_call(item_id, new_position):
#         print(f"Calling external API for item {item_id} to set position {new_position}")
#         return {"item_id": item_id, "new_position": new_position, "status": "success"}

#     # Find items with changed positions and make API calls
#     changes = [
#         item for item in items if item["starting_position"] != item["current_position"]
#     ]
#     for item in changes:
#         response = external_api_call(item["id"], item["current_position"])
#         print(response)

#     # Update starting_position and clear history
#     for item in items:
#         item["starting_position"] = item["current_position"]
#         item["history"].clear()
#         item["history"].append(item["current_position"])

#     set_items(items)
#     return jsonify({
#         "success": True,
#         "message": "Finalized changes.",
#         "changed_items": [
#             {
#                 "id": item["id"],
#                 "label": item["label"],
#                 "starting_position": item["starting_position"],
#                 "current_position": item["current_position"],
#                 "history": list(item["history"])
#             }
#             for item in changes
#         ]
#     })