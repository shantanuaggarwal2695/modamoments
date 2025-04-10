// Check API health status when the page loads
document.addEventListener('DOMContentLoaded', function() {
    checkApiStatus();
});

/**
 * Check the health status of the API
 */
function checkApiStatus() {
    const statusElement = document.getElementById('apiStatus');
    if (!statusElement) return;
    
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'healthy') {
                statusElement.innerHTML = `
                    <div class="alert alert-success">
                        <strong>API Status:</strong> Healthy
                        <br>
                        <strong>OpenAI Connection:</strong> Connected
                    </div>
                `;
            } else {
                statusElement.innerHTML = `
                    <div class="alert alert-warning">
                        <strong>API Status:</strong> Degraded
                        <br>
                        <strong>OpenAI Connection:</strong> ${data.openai_connection}
                        <br>
                        <strong>Error:</strong> ${data.error || 'Unknown error'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error checking API status:', error);
            statusElement.innerHTML = `
                <div class="alert alert-danger">
                    <strong>API Status:</strong> Unavailable
                    <br>
                    <strong>Error:</strong> Could not connect to API
                </div>
            `;
        });
}
