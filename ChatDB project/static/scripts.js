document.getElementById('queryForm').addEventListener('submit', function(event) {
    event.preventDefault();

    let formData = new FormData(this);
    fetch('/submit_query', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('query-results').style.display = 'block';
        document.getElementById('generatedQuery').textContent = data.generated_query;
        let resultBody = document.getElementById('resultBody');
        resultBody.innerHTML = ''; // Clear previous results

        data.result.forEach(row => {
            let tr = document.createElement('tr');
            let tdField = document.createElement('td');
            tdField.textContent = row.Field;
            let tdValue = document.createElement('td');
            tdValue.textContent = row.Value;
            tr.appendChild(tdField);
            tr.appendChild(tdValue);
            resultBody.appendChild(tr);
        });
    });
});
