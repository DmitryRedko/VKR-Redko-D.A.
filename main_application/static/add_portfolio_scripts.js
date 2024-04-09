
function addRemoveStockRow(button) {
    var row = button.parentNode.parentNode;
    row.parentNode.removeChild(row);
    addDisableSelectedTickers();
}

function addCollectTickers() {
    var selectedTickers = [];
    var selectElements = document.querySelectorAll('select[name="ticker"]');
    selectElements.forEach(function(selectElement) {
        if (selectElement.value !== "") {
            selectedTickers.push(selectElement.value);
        }
    });
    var tickersInput = document.createElement("input");
    tickersInput.setAttribute("type", "hidden");
    tickersInput.setAttribute("name", "selected_tickers");
    tickersInput.setAttribute("value", selectedTickers.join(","));
    document.getElementById("add-portfolio-form").appendChild(tickersInput);
}

function addFetchPurchasePrice(selectElement, priceDiv) {
    var ticker = selectElement.value;
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/get_purchase_price?ticker=" + ticker, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            priceDiv.innerText = xhr.responseText;
        }
    };
    xhr.send();
}

function addFetchSentimen(selectElement, sentimentDiv) {
    var ticker = selectElement.value;
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/get_sentiment?ticker=" + ticker, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            sentimentDiv.innerText = xhr.responseText;

            // Remove previous color classes
            sentimentDiv.classList.remove('positive', 'negative');

            // Add appropriate color class based on sentiment value
            if (sentimentValue < 0) {
                sentimentDiv.classList.add('negative');
            } else {
                sentimentDiv.classList.add('positive');
            }
        }
        
    };
    xhr.send();
}


function addFetchAssetPrice(selectElement, assetPriceDiv) {
    var ticker = selectElement.value;
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/get_purchase_price?ticker=" + ticker, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            assetPriceDiv.innerText = xhr.responseText;
        }
    };
    xhr.send();
}

function addUpdateTotal(inputElement) {
    var quantity = inputElement.value;
    var ticker = inputElement.parentNode.parentNode.querySelector('select[name="ticker"]').value;
    var priceDiv = inputElement.parentNode.parentNode.querySelector('.purchase-price-div'); 
    if (!priceDiv) {
        
        var currentRow = inputElement.parentNode.parentNode;
        var cells = currentRow.getElementsByTagName('td');
        for (var i = 0; i < cells.length; i++) {
            var cell = cells[i];
            if (cell.querySelector('.purchase-price-div')) {
                priceDiv = cell.querySelector('.purchase-price-div');
                break;
            }
        }
    }
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/get_purchase_price?ticker=" + ticker, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var price = parseFloat(xhr.responseText);
            if (!isNaN(price) && quantity > 0) {
                var totalPrice = price * quantity;
                priceDiv.innerText = totalPrice.toFixed(2); 
            }
        }
    };
    xhr.send();
}

function addDisableSelectedTickers() {
    var options = document.querySelectorAll('#add-stocks-table-body select[name="ticker"] option');
    var selectedTickers = addGetAllTickers();
    options.forEach(function(option) {
        if (selectedTickers.includes(option.value)) {
            option.disabled = true;
        } else {
            option.disabled = false;
        }
    });
}

function addHandleTickerChange(selectElement) {
    var quantityInput = selectElement.parentNode.parentNode.querySelector('input[name="quantity"]');
    var priceDiv = selectElement.parentNode.parentNode.querySelector('.purchase-price-div');
    var assetPriceDiv = selectElement.parentNode.parentNode.querySelector('.asset-price-div'); 
    var sentimentDiv = selectElement.parentNode.parentNode.querySelector('.sentiment-div'); 
    quantityInput.value = 1;
    quantityInput.disabled = false;
    addFetchPurchasePrice(selectElement, priceDiv);
    addFetchAssetPrice(selectElement, assetPriceDiv); 
    
    setTimeout(function() {
        addFetchSentimen(selectElement, sentimentDiv);
    }, 10); // Delay of 10 millisecond

    addDisableSelectedTickers();
}

function addGetAllTickers() {
    var tickers = [];
    var selectElements = document.querySelectorAll('table#add-stocks-table select[name="ticker"]');
    selectElements.forEach(function(selectElement) {
        var ticker = selectElement.value;
        if (ticker !== "") {
            tickers.push(ticker);
        }
    });
    return tickers;
}

document.getElementById("add-portfolio-form").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
    }
});


