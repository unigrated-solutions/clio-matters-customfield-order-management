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
    font-size: 1.3em;
    font-weight: bold;
    color: #333;
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
    padding: 10px;
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
    border-radius: 5px;
    border: 2px solid #ccc;
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
    padding: 0;
}

.field-card {
    width: 100%;
    align-items: center;
    cursor: pointer;
    transition: background-color 0.3s;
    padding: 0;
    margin: 0; /* top, right, bottom, left */
}

.custom-select .q-field__native,
.custom-select .q-placeholder,
.custom-select .q-field__label {
    font-size: 1.2em;
    font-weight: bold;
}
'''