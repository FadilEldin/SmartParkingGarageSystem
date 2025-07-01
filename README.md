# Parking Garage Management System

A comprehensive web-based parking garage management system built with Flask, MongoDB, and vanilla JavaScript. The system allows users to park cars, exit cars, find parked vehicles, and visualize garage layouts across multiple floors.

## Features

- **Multi-floor garage management** with bay-based organization
- **Car parking** with size compatibility checking
- **Vehicle exit** with automatic fee calculation
- **Car location finder** with detailed information
- **Real-time garage status** display
- **Visual floor layouts** with interactive spot visualization
- **Multiple spot types**: Compact, Standard, Oversized, EV Charging
- **Detailed fee breakdown** with hourly rates and duration tracking

## Technology Stack

- **Backend**: Python Flask
- **Database**: MongoDB
- **Frontend**: HTML, CSS (Bootstrap), Vanilla JavaScript
- **Data Modeling**: PyMongo with custom enums

## Project Structure

```
parking-garage/
├── app.py              # Main Flask application
├── models.py           # Database models and enums
├── services.py         # Business logic layer
├── static/
│   └── js/
│       └── scripts.js  # Frontend JavaScript
└── templates/
    ├── index.html      # Main dashboard
    └── floor.html      # Floor visualization
```

## Installation & Setup

### Prerequisites
- Python 3.7+
- MongoDB 4.0+
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd parking-garage
   ```

2. **Install Python dependencies**
   ```bash
   pip install flask pymongo python-dotenv
   ```

3. **Set up MongoDB**
   - Install MongoDB on your system
   - Start MongoDB service
   - Create a database named `parking_garage`

4. **Configure environment variables**
   ```bash
   # Optional: Set custom MongoDB URI
   export MONGO_URI="mongodb://localhost:27017/"
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open browser to `http://localhost:3333`

## Database Schema

### Collections

#### `floors`
```javascript
{
  "floor_number": 1,
  "bays": [
    {
      "bay_id": "A",
      "spots": [
        {
          "spot_id": "1-A-1",
          "type": "standard",
          "status": "available"
        }
      ]
    }
  ]
}
```

#### `cars`
```javascript
{
  "license_plate": "ABC123",
  "spot_id": "1-A-1",
  "car_size": "medium",
  "checkin_time": "2025-01-01T10:00:00",
  "checkout_time": null,
  "fee": 0
}
```

## API Endpoints

### Spots Management
- `GET /v1/api/spots` - Get all parking spots with status
- `GET /v1/api/spots/available` - Get available spots (optional type filter)

### Car Operations
- `POST /v1/api/cars/park` - Park a car
- `POST /v1/api/cars/exit` - Exit a car and calculate fee
- `GET /v1/api/cars/find` - Find a parked car by license plate

### Visualization
- `GET /floor/<floor_number>` - View specific floor layout

## Usage Examples

### Parking a Car
```bash
curl -X POST http://localhost:3333/v1/api/cars/park \
  -H "Content-Type: application/json" \
  -d '{"license_plate": "ABC123", "car_size": "medium"}'
```

### Finding a Car
```bash
curl "http://localhost:3333/v1/api/cars/find?license_plate=ABC123"
```

### Exiting a Car
```bash
curl -X POST http://localhost:3333/v1/api/cars/exit \
  -H "Content-Type: application/json" \
  -d '{"license_plate": "ABC123"}'
```

## Business Logic

### Car Size Compatibility
- **Small cars**: Can park in compact, standard, oversized spots
- **Medium cars**: Can park in standard, oversized spots  
- **Large cars**: Can only park in oversized spots

### Pricing Structure
- **Compact spots**: $5/hour
- **Standard spots**: $7/hour
- **Oversized spots**: $10/hour
- **EV Charging spots**: $8/hour

### Spot Allocation
The system automatically finds the first available compatible spot when parking a car.

## Features in Detail

### Dashboard (`/`)
- Park new vehicles
- Exit parked vehicles with fee calculation
- Find specific vehicles
- View real-time garage status
- Access floor visualizations

### Floor Visualization (`/floor/<number>`)
- Visual representation of garage floor
- Color-coded spot status
- Vehicle information display
- Real-time updates

### Fee Calculation
Displays detailed breakdown: `$9.50 [$7/hr × 1.36 hrs = $9.50 (standard spot, medium car)]`

### Duration Display
Shows parking duration in `HH:MM:SS` format for better readability.

## Default Garage Layout

The system initializes with:
- **2 floors**
- **4 bays total** (2 per floor)
- **20 spots total** (5 per bay)
- **Mixed spot types** across different bays

## Error Handling

- Invalid car sizes
- No available compatible spots
- Car not found scenarios
- Database connection issues
- Missing required fields

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For issues and questions, please create an issue in the GitHub repository.