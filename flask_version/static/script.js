$(document).ready(function () {
    let selectedItems = [];
    let targetItem = null;
    let lastSelectedIndex = null; // Track the index of the last clicked item


    // Fetch items and item sets when the page loads
    $.ajax({
        url: '/load-fields',
        method: 'POST',
        success: function (data) {
            populateFieldSetList(data.item_sets); // Populate left list
            populateCustomfieldList(data.items);   // Populate right list
            updateCounts()
        },
        error: function () {
            alert('Failed to load fields. Please try again.');
        },
    });

    function populateFieldSetList(itemSets) {
        const container = $('#scrollable-tables');
        container.empty(); // Clear any existing content
    
        itemSets.forEach(itemSet => {
            const rows = chunkArray(itemSet.ordered_items, 2); // Group items into chunks of 2
            const setHtml = `
                <div class="item-set-container">
                    <h3 class="item-set-label">
                        ${itemSet.label}
                    </h3>
                    <table class="item-set-table">
                        <tbody>
                            ${rows.map(row => `
                                <tr>
                                    ${row.map(item => {
                                        // Check if the item is deleted and append "(deleted)"
                                        const label = item ? (item.deleted ? `${item.label} (deleted)` : item.label) : '';
                                        return `<td>${label}</td>`;
                                    }).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>`;
            container.append(setHtml);
        });
    }
    
    // Event delegation for collapsible tables
    $(document).on('click', '.item-set-label', function () {
        const table = $(this).next('.item-set-table'); // Find the next sibling table
        table.toggle(); // Show or hide the table
    });

    // Utility function to split an array into chunks of a specified size
    function chunkArray(array, size) {
        const chunks = [];
        for (let i = 0; i < array.length; i += size) {
            chunks.push(array.slice(i, i + size));
        }
        return chunks;
    }

    // Function to populate the right list
    function populateCustomfieldList(items) {
        const container = $('#item-list');
        container.empty(); // Clear any existing content

        items.forEach(item => {
            // Add "(deleted)" if the item is marked as deleted
            const label = item.deleted ? `${item.label} (deleted)` : item.label;

            const itemHtml = `
                <div class="item" data-id="${item.id}" data-current-position="${item.current_position}">
                    <div class="item-left">
                        <span class="item-label">${label}</span>
                    </div>
                    <div class="item-right">
                        <span class="position-info">Current: ${item.current_position}</span>
                        <span class="position-info">Starting: ${item.starting_position}</span>
                    </div>
                </div>`;
            container.append(itemHtml);
        });
    }


    // Update counts (matches and selected)
    function updateCounts() {
        const visibleItems = $('.item:visible').length;
        const selectedItems = $('.item.selected').length;

        $('#match-count').text(`Matches: ${visibleItems}`);
        $('#selected-count').text(`Selected: ${selectedItems}`);
    }

    // Prevent text selection during Shift+Click
    $(document).on('mousedown', '.item', function (e) {
        if (e.shiftKey) {
            e.preventDefault(); // Prevent text selection
        }
    });

    // Update selected count whenever an item is clicked
    $(document).on('click', '.item', function (e) { // Pass the event object here
        const id = $(this).data('id');
        const position = $(this).data('current-position');
        const items = $('.item:visible'); // Only visible items are considered
        const clickedIndex = items.index(this); // Index of the clicked item
        const searchTerm = $('#item-search').val().trim();
        let lastSelectedIndex = items.index($('.item.selected:visible').last());

        if (e.shiftKey) {
            // Shift key: Select a range of items
            if (lastSelectedIndex !== -1) {
                const start = Math.min(lastSelectedIndex, clickedIndex);
                const end = Math.max(lastSelectedIndex, clickedIndex);
                items.slice(start, end + 1).each(function () {
                    if (!$(this).hasClass('selected')) {
                        $(this).addClass('selected');
                        selectedItems.push({
                            id: $(this).data('id'),
                            position: $(this).data('current-position'),
                        });
                    }
                });
            }
        } else if (e.ctrlKey || e.metaKey || searchTerm.length > 0) {
            // Ctrl/Command key or when a search term is active: Toggle the clicked item
            if ($(this).hasClass('selected')) {
                // Deselect the item
                $(this).removeClass('selected');
                selectedItems = selectedItems.filter(item => item.id !== id);
            } else {
                // Select the item
                $(this).addClass('selected');
                selectedItems.push({ id, position });
            }
        } else {
            // No modifier key and search input is empty: Clear all selections and select only the clicked item
            $('.item').removeClass('selected'); // Deselect all visible items
            selectedItems = []; // Clear the selectedItems array
            $(this).addClass('selected'); // Select the clicked item
            selectedItems.push({ id, position });
        }

        // Update the selected count display
        const selectedCount = $('.item.selected').length;
        $('#selected-count').text(`Selected: ${selectedCount}`);
    });

        // Search functionality
    $('#item-search').on('input', function () {
        const searchTerm = $(this).val().toLowerCase().trim();

        $('.item').each(function () {
            const label = $(this).find('span:first').text().toLowerCase();
            if (searchTerm.length === 0 || label.includes(searchTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });

        updateCounts(); // Update counts after search
    });

    // Context menu for right-click
    $(document).on('contextmenu', '.item', function (e) {
        e.preventDefault();
        targetItem = $(this).data('id'); // Set target item
        const menu = $('#context-menu');
        menu.css({ top: e.pageY, left: e.pageX }).show();
    });

    // Hide context menu when clicking elsewhere
    $(document).on('click', function (e) {
        if (!$(e.target).closest('#context-menu').length) {
            $('#context-menu').hide();
        }
    });

    // Insert items before or after the target
    $('#insert-before, #insert-after').click(function () {
        console.log('Selected Items:', selectedItems);

        if (!selectedItems.length || !targetItem) {
            console.log('No items selected or target item not specified.');
            return;
        }

        const position = $(this).attr('id') === 'insert-before' ? 'before' : 'after';
        const movingIds = selectedItems.map(item => item.id); // IDs of selected items
        const targetElement = $(`.item[data-id="${targetItem}"]`);
        const targetPosition = targetElement.data('current-position'); // Target's current position

        if (targetPosition === undefined) {
            alert('Target item position is undefined.');
            console.log('Error: Target item position is undefined.');
            return;
        }

        let insertPosition;

        if (position === 'before') {
            // Insert before the target position
            insertPosition = targetPosition;
        } else if (position === 'after') {
            // Insert after the target position
            insertPosition = targetPosition + 1;
        }

        // Log details for debugging
        console.log('Action:', position);
        console.log('Selected Item IDs:', movingIds);
        console.log('Target Item ID:', targetItem);
        console.log('Target Position:', targetPosition);
        console.log('Insert Position:', insertPosition);

        // Send the update to the server
        $.ajax({
            url: '/update-order',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                moving_ids: movingIds,
                target_position: insertPosition,
            }),
            success: function () {
                console.log('Update successful. Reloading page.');
                location.reload();
            },
            error: function () {
                console.error('An error occurred while updating the order.');
                alert('An error occurred while updating the order.');
            },
        });
    });


    // Scroll button functionality
    $('#scroll-up').click(function () {
        const container = $('#item-list-container');
        container.scrollTop(container.scrollTop() - container.height());
    });

    $('#scroll-down').click(function () {
        const container = $('#item-list-container');
        container.scrollTop(container.scrollTop() + container.height());
    });
});