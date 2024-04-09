function changeUpdateTotal(inputElement) {
    var quantity = inputElement.value;
    var row = inputElement.parentNode.parentNode;
    
    var ticker = row.cells[1].innerText; 
    var quantity = parseFloat(row.cells[2].innerText); 
    var purchasePrice = parseFloat(row.cells[3].innerText); 
    var totalCost = parseFloat(row.cells[4].innerText); 
    var percent = parseFloat(row.cells[5].innerText); 
    var currentPrice = parseFloat(row.cells[6].innerText); 


    var currentQuantity = parseFloat(row.cells[7].querySelector('input[type="number"]').value); 
    var newCurrentPrice = row.cells[8]; 
    var currentTotalCost = row.cells[9]; 
    
    console.log("Ticker:", ticker);
    console.log("Quantity:", quantity);
    console.log("Purchase Price:", purchasePrice);
    console.log("Total Cost:", totalCost);
    console.log("Percent:", percent);
    console.log("Current Price:", currentPrice);
    console.log("Current Quantity:", currentQuantity);
    console.log("New Current Price:", newCurrentPrice.innerText);
    console.log("Current Total Cost:", currentTotalCost.innerText);

    var new_quantity = (currentQuantity-quantity)
    if (new_quantity<0 || isNaN(new_quantity))
        new_quantity = 0;

    newCurrentPrice.innerHTML = "<div name=\"new-purchase-price\">"+((quantity * purchasePrice + new_quantity*currentPrice)/(quantity+new_quantity)).toFixed(2)+"</div>";

    currentTotalCost.innerHTML = "<div name=\"new-total-cost\">"+(quantity * purchasePrice + new_quantity*currentPrice).toFixed(2)+"</div>";

    updatePercent();

}

function refreshPage() {
    window.location.reload();
}


function prepareFormData(inputElement) {
    var rows = document.querySelectorAll('#change-stocks-table-body tr');

    var currentDateDiv = document.querySelector('div[hidden]');
    var currentDate = currentDateDiv.innerText;

    var formData = {};
    var index = 0;

    
    for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        try {
            var purchaseDate = row.querySelector('div[name="old-purchase-date"]').innerText;
            var ticker = row.querySelector('div[name="ticker"]').innerText;
            var oldQuantity = row.querySelector('div[name="old-quantity"]').innerText;
            var oldPurchasePrice = row.querySelector('div[name="old-purchase-price"]').innerText;
            var oldTotalCost = row.querySelector('div[name="old-total-cost"]').innerText;
            var newPurchasePrice = row.querySelector('div[name="new-purchase-price"]').innerText;
            var currentPrice = row.querySelector('div[name="current_price"]').innerText;
            var newQuantity = row.querySelector('input[name="new-quantity"]').value;
            
            var date = purchaseDate;

            if( newQuantity > oldQuantity && newQuantity > 0 && !isNaN(newQuantity))
                date = currentDate;
            
            var rowData = {
                'purchase_date': date,
                'ticker': ticker,
                'old_quantity': oldQuantity,
                'old_purchase_price': oldPurchasePrice,
                'old_total_cost': oldTotalCost,
                'current_price': currentPrice,
                'new_purchase_price': newPurchasePrice,
                'new_quantity': newQuantity
            };

            console.log(index);
            console.log(rowData);
            
            formData["row_"+index] = rowData;
            index+=1;

        } catch {
            console.log("Ошибка")
        };

        try {
            parseFloat(newQuantity);
            if(newQuantity<=0){
                console.log("Ошибка")
                return true;
            }
        }
        catch{
            console.log("Ошибка")
            return true;
        }
        
    };

    for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        try {
            var purchaseDate = row.querySelector('input[name="purchase-date"]').value;
            var ticker = row.querySelector('select[name="ticker"]').value;
            var newQuantity = row.querySelector('input[name="quantity"]').value;
                
            var rowData = {
                'purchase_date': purchaseDate,
                'ticker': ticker,
                'old_quantity': "", 
                'old_purchase_price': "",
                'old_total_cost': "",
                'current_price': "",
                'new_purchase_price': "",
                'new_quantity': newQuantity
            };

            console.log(index);
            console.log(rowData);
            
            formData["new_row_"+index] = rowData;
            index+=1;
        } catch {
            console.log("Ошибка")
        };

        try {
            parseFloat(newQuantity);
            if(ticker="" || newQuantity<=0 || isNaN(newQuantity)){
                console.log("Ошибка")
                return true;
            }
        }
        catch{
            console.log("Ошибка")
            return true;
        }

    };
    

    console.log(JSON.stringify(formData));
    
    axios.post('/process_form_data', {
        data: formData
    })
    .then(function (response) {
        console.log(response);
    })
    .catch(function (error) {
        console.log(error);
    });

    setTimeout(refreshPage, 100);

    return false;
}

function updatePercent() {
    var totalSum = 0;
    var rows = document.querySelectorAll('#change-stocks-table-body tr');
    rows.forEach(function(row) {
        var currentTotalCost = parseFloat(row.cells[9].innerText);
        totalSum += currentTotalCost;
    });

    rows.forEach(function(row) {
        var currentTotalCost = parseFloat(row.cells[9].innerText);
        var percentCell = row.cells[10];
        var percent = (currentTotalCost / totalSum * 100).toFixed(2);
        percentCell.innerText = percent + '%';
    });
}

document.addEventListener("DOMContentLoaded", function() {
    var inputElements = document.querySelectorAll('#change-stocks-table-body input[type="number"]');
    inputElements.forEach(function(inputElement) {
        changeUpdateTotal(inputElement);
    });
});



function changeRemoveStockRow(button) {
    var row = button.parentNode.parentNode;
    row.parentNode.removeChild(row);
    changeDisableSelectedTickers();
}

function changeCollectTickers() {
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
    document.getElementById("change-portfolio-form").appendChild(tickersInput);
}

function changeFetchPurchasePrice(selectElement, priceDiv) {
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

function changeFetchAssetPrice(selectElement, assetPriceDiv) {
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

function changeUpdateTotalNew(inputElement) {
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

function changeDisableSelectedTickers() {
    var options = document.querySelectorAll('#change-stocks-table-body select[name="ticker"] option');
    var selectedTickers = changeGetAllTickers();
    options.forEach(function(option) {
        if (selectedTickers.includes(option.value)) {
            option.disabled = true;
        } else {
            option.disabled = false;
        }
    });
}

function changeHandleTickerChange(selectElement) {
    var quantityInput = selectElement.parentNode.parentNode.querySelector('input[name="quantity"]');
    var priceDiv = selectElement.parentNode.parentNode.querySelector('.purchase-price-div');
    var assetPriceDiv = selectElement.parentNode.parentNode.querySelector('.asset-price-div'); 
    quantityInput.value = 1;
    quantityInput.disabled = false;
    changeFetchPurchasePrice(selectElement, priceDiv);
    changeFetchAssetPrice(selectElement, assetPriceDiv); 
    changeDisableSelectedTickers();
}

function changeGetAllTickers() {
    var tickers = [];
    var selectElements = document.querySelectorAll('table#change-stocks-table select[name="ticker"]');
    selectElements.forEach(function(selectElement) {
        var ticker = selectElement.value;
        if (ticker !== "") {
            tickers.push(ticker);
        }
    });

    // Добавление уже имеющихся тикеров
    var existingTickers = document.querySelectorAll('table#change-stocks-table tbody#change-stocks-table-body td:nth-child(2)');
    existingTickers.forEach(function(tickerElement) {
        var ticker = tickerElement.innerText;
        if (!tickers.includes(ticker)) {
            tickers.push(ticker);
        }
    });

    return tickers;
}

document.getElementById("change-portfolio-form").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
    }
});


