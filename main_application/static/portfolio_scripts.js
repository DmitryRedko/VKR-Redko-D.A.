
function removeStockRow(button) {
    var row = button.parentNode.parentNode;
    row.parentNode.removeChild(row);
    disableSelectedTickers();
}

function collectTickers() {
    var selectedTickers = [];
    var selectElements = document.querySelectorAll('select[name="ticker"]');
    selectElements.forEach(function(selectElement) {
        if (selectElement.value !== "") {
            selectedTickers.push(selectElement.value);
        }
    });
    // Добавляем выбранные тикеры в скрытое поле формы для отправки на сервер
    var tickersInput = document.createElement("input");
    tickersInput.setAttribute("type", "hidden");
    tickersInput.setAttribute("name", "selected_tickers");
    tickersInput.setAttribute("value", selectedTickers.join(","));
    document.getElementById("add-portfolio-form").appendChild(tickersInput);
}


function fetchPurchasePrice(selectElement, priceDiv) {
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

function updateTotal(inputElement) {
    var quantity = inputElement.value;
    var ticker = inputElement.parentNode.parentNode.querySelector('select[name="ticker"]').value;
    var priceDiv = inputElement.parentNode.nextElementSibling.querySelector('.purchase-price-div'); 
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/get_purchase_price?ticker=" + ticker, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var price = parseFloat(xhr.responseText);
            if (!isNaN(price) && quantity > 0) {
                var totalPrice = price * quantity;
                priceDiv.innerText = totalPrice.toFixed(1); 
            }
        }
    };
    xhr.send();
}


function disableSelectedTickers() {
    var options = document.querySelectorAll('#stocks-table-body select[name="ticker"] option');
    var selectedTickers = getAllTickers();
    options.forEach(function(option) {
        if (selectedTickers.includes(option.value)) {
            option.disabled = true;
        } else {
            option.disabled = false;
        }
    });
}

function handleTickerChange(selectElement) {
    var quantityInput = selectElement.parentNode.parentNode.querySelector('input[name="quantity"]');
    var priceDiv = selectElement.parentNode.parentNode.querySelector('.purchase-price-div');
    quantityInput.value = 1;
    quantityInput.disabled = false;
    fetchPurchasePrice(selectElement, priceDiv);
    disableSelectedTickers();
}

function getAllTickers() {
    var tickers = [];
    var selectElements = document.querySelectorAll('table#stocks-table select[name="ticker"]');
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

