// JavaScript to handle status updates and PDF download
var socket = io.connect(window.location.origin); // Declare socket once

socket.on('update', function(data) {
    const fileName = data.file;
    const status = data.status;
    let statusList = document.getElementById('status-list');
    let listItem = document.getElementById(fileName);

    if (listItem) {
        listItem.querySelector('.badge-status').textContent = status;
        listItem.querySelector('.badge-status').className = 'badge badge-status ' + 
            (status === 'Completed' ? 'bg-success' : (status === 'Failed' ? 'bg-danger' : 'bg-warning'));

        if (status === 'Completed') {
            // Create a link to the PDF file
            const downloadLink = document.createElement('a');
            downloadLink.href = '/download/' + fileName.replace(/\.(csv|docx|pdf)$/i, '.pdf');
            downloadLink.textContent = 'Open PDF';
            downloadLink.className = 'btn btn-link ms-3'; // Optional styling
            downloadLink.target = '_blank'; // Opens the link in a new tab

            // Automatically download the PDF
            downloadLink.setAttribute('download', fileName.replace(/\.(csv|docx|pdf)$/i, '.pdf'));

            // Trigger the automatic download
            downloadLink.click();

            listItem.appendChild(downloadLink);
        }
    } else {
        // If the list item doesn't exist, create it and append it to the list
        listItem = document.createElement('li');
        listItem.id = fileName;
        listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
        listItem.innerHTML = `${fileName} <span class="badge badge-status bg-warning">${status}</span>`;
        statusList.appendChild(listItem);
    }
});