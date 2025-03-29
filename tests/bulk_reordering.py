# items = [
#     {'id': 'A', 'display_order': 0},
#     {'id': 'B', 'display_order': 1},
#     {'id': 'C', 'display_order': 2},
#     {'id': 'D', 'display_order': 3},
#     {'id': 'E', 'display_order': 4},
#     {'id': 'F', 'display_order': 5},
# ]

items = [{'id': chr(i), 'display_order': i - 65} for i in range(65, 91)]


def log_display_order_change(item_id, new_order):
    print(f"Moving item '{item_id}' to new display_order: {new_order}")
    return True  # Simulate a successful result

def move_item(moving_id, target_id, position, on_display_order_change):
    global items
    items = sorted(items, key=lambda x: x['display_order'])

    moving_item = next(item for item in items if item['id'] == moving_id)
    target_item = next(item for item in items if item['id'] == target_id)

    moving_order = moving_item['display_order']
    target_order = target_item['display_order']

    if moving_order == target_order:
        return True

    if moving_order < target_order:
        if position == 'after':
            new_order = target_order
            success = on_display_order_change(moving_id, new_order)
            if success:
                for item in items:
                    if item['id'] == moving_id:
                        item['display_order'] = new_order
                    elif moving_order < item['display_order'] <= target_order:
                        item['display_order'] -= 1
                return True

        elif position == 'before':
            new_order = target_order - 1
            success = on_display_order_change(moving_id, new_order)
            if success:
                for item in items:
                    if item['id'] == moving_id:
                        item['display_order'] = new_order
                    elif moving_order < item['display_order'] < target_order:
                        item['display_order'] -= 1
                return True

    elif moving_order > target_order:
        if position == 'after':
            new_order = target_order + 1
            success = on_display_order_change(moving_id, new_order)
            if success:
                for item in items:
                    if item['id'] == moving_id:
                        item['display_order'] = new_order
                    elif target_order < item['display_order'] < moving_order:
                        item['display_order'] += 1
                return True

        elif position == 'before':
            new_order = target_order
            success = on_display_order_change(moving_id, new_order)
            if success:
                for item in items:
                    if item['id'] == moving_id:
                        item['display_order'] = new_order
                    elif target_order <= item['display_order'] < moving_order:
                        item['display_order'] += 1
                return True

    return False


def bulk_move_items(moving_ids, target_id, position):
    # Sort moving_ids by their current display_order
    id_to_order = {item['id']: item['display_order'] for item in items}
    moving_ids = sorted(moving_ids, key=lambda x: id_to_order[x])

    first_move_complete = False
    for id in moving_ids:
        if not first_move_complete:
            success = move_item(id, target_id, position, log_display_order_change)
            if success:
                first_move_complete = True
                position = 'after'
                target_id = id
        else:
            success = move_item(id, target_id, position, log_display_order_change)
            if success:
                target_id = id


########################################
######## Bulk Reordering ###############
# # List of moves to perform in sequence
# moves = [
#     ('F', 'D', 'after'),
#     ('A', 'C', 'before'),
#     ('E', 'B', 'after'),
#     ('B', 'D', 'before'),
# ]

# print("Starting order:")
# for item in sorted(items, key=lambda x: x['display_order']):
#     print(item)
    
# # Perform each move
# for moving_id, target_id, position in moves:
#     print(f'\nMove: {moving_id} -> {position} {target_id}')
#     move_item(moving_id, target_id, position, log_display_order_change)
#     print("New order:")
#     for item in sorted(items, key=lambda x: x['display_order']):
#         print(item)
        
# print("\nFinal item order:")
# for item in sorted(items, key=lambda x: x['display_order']):
#     print(item)
#############################################

##########################################
###### Bulk Grouping and Reordering ######    
bulk_move_id_list = ['Q', 'J', 'F', 'W', 'C']
target_id = 'M'
position = 'before'

bulk_move_items(bulk_move_id_list, target_id, position)
 
print("\nFinal item order:")
for item in sorted(items, key=lambda x: x['display_order']):
    print(item)
    
##############################################