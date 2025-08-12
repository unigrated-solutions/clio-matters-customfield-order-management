styles = '''
.custom-field-card {
    width: 100%;
    cursor: pointer;
    transition: background-color 0.3s;
    padding: 5px;
    background-color: white; /* default */
}

.custom-field-card.selected {
    background-color: lightblue; /* selected highlight */
}

.custom-field-name-label {
    font-size: 1.3em !important;
    font-weight: bold !important;
    color: #333 !important;
}

.page-container {
    width: 100%;
    height: calc(100vh - 100px);
    margin: 0;
    padding: 5px 2px;
    display: flex;
}

.full-height-container {
    flex: 1;
    gap: 0;
    height: 100%;
    padding: 1px;
    margin: 0;
    display: flex;
    flex-direction: column;
    background-color: WhiteSmoke;
}

.scroll-container {
    flex: 1;
    width: 100%;
    gap: 0;
    padding: 0;
    margin: 0;

}

.scroll-content {
    display: flex;
    width: 100%;
    flex-direction: column;
    gap: 2px;
    margin: 0;
    padding: 0;
}

.filter-box {
    flex: 1 1 200px;
    min-width: 150px;
    max-width: 300px;
    border-radius: 5px;
    border: 2px solid #ccc;
    padding: 0 10px 0 10px;
}

.field-card {
    width: 100%;
    align-items: center;
    cursor: pointer;
    transition: background-color 0.3s;
    padding: 0;
    margin: 0;
}

.field-card:hover {
    background-color: #f2f2f2; /* light gray */
}

.field-label {
    font-size: 1.3em !important;
    font-weight: bold !important;
    color: #333 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    border: 1px solid #ccc !important;
    border-radius: 0.25rem !important;
    padding: 0.5rem !important;
    background-color: white !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    cursor: pointer !important;
    height: 100% !important;
    transition: background-color 0.3s !important;
}

.field-label:hover {
    background-color: #f2f2f2 !important;
}

.column-footing {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    background-color: white;
    border: 2px solid #D1D5DB; /* Tailwind's gray-300 */
    border-radius: 0.5rem;
    padding: 4px 10px 4px 10px; /* top right bottom left */
}

.custom-select .q-field__native,
.custom-select .q-placeholder,
.custom-select .q-field__label {
    font-size: 1.2em;
    font-weight: bold;
}

.header-button {
    height: 35px; 
    width: 35px;
}

.clear-icon {
    cursor: pointer;
}

'''