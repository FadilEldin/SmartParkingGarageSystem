// Load floors for visualization dropdown
function loadFloors() {
    fetch('/v1/api/spots')
        .then(response => response.json())
        .then(data => {
            const uniqueFloors = [...new Set(data.map(spot => spot.floor))];
            const floorSelect = document.getElementById('floorSelect');

            uniqueFloors.forEach(floor => {
                const option = document.createElement('option');
                option.value = floor;
                option.textContent = `Floor ${floor}`;
                floorSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error:', error));
}

// Handle visualize button click
document.getElementById('visualizeBtn').addEventListener('click', function() {
    const floorNumber = document.getElementById('floorSelect').value;
    if (floorNumber) {
        window.open(`/floor/${floorNumber}`, '_blank');
    } else {
        alert('Please select a floor first');
    }
});


document.addEventListener('DOMContentLoaded', function() {
    loadFloors()
    // Park Car Form
    document.getElementById('parkForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const licensePlate = document.getElementById('licensePlate').value;
        const carSize = document.getElementById('carSize').value;
        
        fetch('/v1/api/cars/park', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ license_plate: licensePlate, car_size: carSize })
        })
        .then(response => response.json())
        .then(data => {
            const messageEl = document.getElementById('parkMessage');
            if (data.error) {
                messageEl.textContent = data.error;
                messageEl.className = 'mt-3 alert alert-danger';
            } else {
                messageEl.textContent = `Car parked at ${data.spot_id} (Floor ${data.floor}, Bay ${data.bay})`;
                messageEl.className = 'mt-3 alert alert-success';
                updateGarageStatus();
            }
            messageEl.style.display = 'block';
        })
        .catch(error => console.error('Error:', error));
    });

    // Exit Car Form
    document.getElementById('exitForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const licensePlate = document.getElementById('exitLicensePlate').value;

    fetch('/v1/api/cars/exit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ license_plate: licensePlate })
    })
    .then(response => response.json())
    .then(data => {
        const exitDetails = document.getElementById('exitDetails');
        if (data.error) {
            alert(data.error);
        } else {
            // Format duration as H:MM:SS
            function formatHMS(seconds) {
                const h = Math.floor(seconds / 3600);
                const m = Math.floor((seconds % 3600) / 60);
                const s = seconds % 60;
                return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
            }
            exitDetails.innerHTML = `
              <h5>Parking Details</h5>
              <div class="receipt">
                <div>Duration: ${formatHMS(data.duration_seconds)} hours</div>
                <div>Fee: $${data.fee.toFixed(2)} ${data.calculation ? `<span class="text-muted">[${data.calculation}]</span>` : ''}</div>
              </div>
            `;
            exitDetails.style.display = 'block';
            updateGarageStatus();
        }
    })
    .catch(error => console.error('Error:', error));
});

    // Find Car Form
    document.getElementById('findForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const licensePlate = document.getElementById('findLicensePlate').value;
        
        fetch(`/v1/api/cars/find?license_plate=${licensePlate}`)
        .then(response => response.json())
        .then(data => {
            const detailsEl = document.getElementById('carDetails');
            if (data.error) {
                detailsEl.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            } else {
                detailsEl.innerHTML = `
                   <div class="card">
                   <div class="card-header">
                       <h5>Car Details</h5>
                   </div>
                   <div class="card-body" style="padding: 1rem;">
                       <div style="line-height: 1.5;">
                           <div><strong>License Plate:</strong> ${data.license_plate || 'Unknown'}</div>
                           <div><strong>Car Size:</strong> ${data.car_size || 'Unknown'}</div>
                           <div><strong>Spot:</strong> ${data.spot_id || 'Unknown'} (Floor ${data.floor || '?'}, Bay ${data.bay || '?'})</div>
                           <div><strong>Spot Type:</strong> ${data.spot_type || 'standard'}</div>
                           <div><strong>Check-in Time:</strong> ${data.checkin_time ? new Date(data.checkin_time).toLocaleString() : 'Unknown'}</div>
                           ${data.checkout_time ? `
                               <div><strong>Check-out Time:</strong> ${new Date(data.checkout_time).toLocaleString()}</div>
                               <div><strong>Fee:</strong> $${data.fee?.toFixed(2) || '0.00'}</div>
                           ` : `
                               <div><strong>Current Duration:</strong> ${data.current_duration_minutes || '0'} minutes</div>
                               <div class="text-success"><strong>Currently Parked</strong></div>
                           `}
                       </div>
                   </div>
               </div>
             `;
            }
            detailsEl.style.display = 'block';
        })
        .catch(error => console.error('Error:', error));
    });

    // Update garage status on page load
    updateGarageStatus();

    // Function to update garage status
    function updateGarageStatus() {
        fetch('/v1/api/spots')
        .then(response => response.json())
        .then(data => {
            const availableSpots = data.filter(spot => spot.status === 'available');
            const occupiedSpots = data.filter(spot => spot.status === 'occupied');
            
            renderSpots('availableSpots', availableSpots);
            renderSpots('occupiedSpots', occupiedSpots);
        })
        .catch(error => console.error('Error:', error));
    }

    // Function to render spots
    function renderSpots(containerId, spots) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (spots.length === 0) {
        container.innerHTML = '<p>No spots found</p>';
        return;
    }

    spots.forEach(spot => {
        const spotEl = document.createElement('div');
        spotEl.className = 'col-md-4 mb-3';

        let spotContent = `
            <div class="card ${spot.status === 'available' ? 'bg-light' : 'bg-warning'}">
                <div class="card-body">
                    <h5 class="card-title">${spot.spot_id}</h5>
                    <p class="card-text">
                        Floor ${spot.floor}, Bay ${spot.bay}<br>
                        Type: ${spot.type}<br>
                        Status: <span class="badge ${spot.status === 'available' ? 'bg-success' : 'bg-danger'}">
                            ${spot.status}
                        </span>
        `;

        // Add license plate and duration for occupied spots
        if (spot.status === 'occupied' && spot.license_plate) {
            spotContent += `
                <br>License: ${spot.license_plate}
                <br>Parked: ${spot.duration_minutes} minutes
            `;
        }

        spotContent += `
                    </p>
                </div>
            </div>
        `;

        spotEl.innerHTML = spotContent;
        container.appendChild(spotEl);
    });
  }
});