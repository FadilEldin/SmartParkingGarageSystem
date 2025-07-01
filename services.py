from flask import jsonify
from datetime import datetime
from models import ParkingSpot, Car, CarSize, SpotType, get_db
from bson import ObjectId

# Initialize database connection
db = get_db()

class ParkingService:
    @staticmethod
    @staticmethod
    def get_all_spots():
        # Get all spots
        spots = list(db.floors.aggregate([
            {"$unwind": "$bays"},
            {"$unwind": "$bays.spots"},
            {"$project": {
                "_id": 0,
                "floor": "$floor_number",
                "bay": "$bays.bay_id",
                "spot_id": "$bays.spots.spot_id",
                "type": "$bays.spots.type",
                "status": "$bays.spots.status"
            }}
        ]))

        # Get car information for occupied spots
        occupied_spots = [s for s in spots if s['status'] == 'occupied']
        for spot in occupied_spots:
            car = db.cars.find_one({"spot_id": spot['spot_id'], "checkout_time": None})
            if car:
                spot['license_plate'] = car['license_plate']
                duration = (datetime.now() - car['checkin_time']).total_seconds() / 60  # in minutes
                spot['duration_minutes'] = int(duration)

        return jsonify(spots)

    @staticmethod
    def get_available_spots(spot_type=None):
        spots = list(ParkingSpot.find_available(spot_type))
        return jsonify(spots)

    @staticmethod
    def park_car(license_plate, car_size):
        # Check if this car is already parked (has an active record)
        existing = db.cars.find_one({
            "license_plate": {"$regex": f"^{license_plate}$", "$options": "i"},
            "checkout_time": None
        })
        if existing:
            return jsonify({"error": "This car is already parked and has not exited."}), 400

        try:
            car_size_enum = CarSize(car_size.lower())
        except ValueError:
            return jsonify({"error": "Invalid car size"}), 400

        # Find all available spots
        all_spots = list(ParkingSpot.find_available())

        # Filter spots by size compatibility
        compatible_spots = [
            spot for spot in all_spots
            if car_size_enum in SpotType(spot['type']).compatible_sizes
        ]

        if not compatible_spots:
            return jsonify({
                "error": f"No available spots compatible with {car_size} cars"
            }), 400

        # Select the first compatible spot (could implement preference logic here)
        spot = compatible_spots[0]

        try:
            car_data = Car.check_in(license_plate, spot["spot_id"], car_size_enum)
            return jsonify({
                "success": True,
                "spot_id": spot["spot_id"],
                "floor": spot["floor"],
                "bay": spot["bay"],
                "type": spot["type"],
                "message": f"{car_size} car parked in {spot['type']} spot"
            })
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @staticmethod
    def exit_car(license_plate):
        result = Car.check_out(license_plate)
        if not result:
            return jsonify({"error": "Car not found or already checked out"}), 404
        return jsonify(result)

    @staticmethod
    def find_car(license_plate):
        try:
            # 1. Try to find active (currently parked) car
            car = db.cars.find_one(
                {"license_plate": {"$regex": f"^{license_plate}$", "$options": "i"}, "checkout_time": None},
                {"_id": 0, "license_plate": 1, "spot_id": 1, "car_size": 1,
                 "checkin_time": 1, "checkout_time": 1, "fee": 1}
            )
            if not car:
                # 2. Fallback: find the latest checked-out record for history
                car = db.cars.find_one(
                    {"license_plate": {"$regex": f"^{license_plate}$", "$options": "i"}},
                    sort=[("checkin_time", -1)],
                    projection={"_id": 0, "license_plate": 1, "spot_id": 1, "car_size": 1,
                                "checkin_time": 1, "checkout_time": 1, "fee": 1}
                )
                if not car:
                    return jsonify({"error": "Car not found"}), 404

            # Validate required fields
            if not car.get("checkin_time"):
                return jsonify({"error": "Car record missing checkin_time"}), 500
            if not car.get("spot_id"):
                return jsonify({"error": "Car record missing spot_id"}), 500

            # 2. Find spot with guaranteed type
            spot_data = db.floors.aggregate([
                {"$unwind": "$bays"},
                {"$unwind": "$bays.spots"},
                {"$match": {"bays.spots.spot_id": car["spot_id"]}},
                {"$project": {
                    "_id": 0,
                    "floor": "$floor_number",
                    "bay": "$bays.bay_id",
                    "type": {"$ifNull": ["$bays.spots.type", "standard"]},
                    "status": "$bays.spots.status"
                }}
            ])

            if not spot_data.alive:
                return jsonify({"error": "Associated spot not found"}), 404

            spot = next(spot_data)

            # 3. Build response with null checks
            response = {
                "license_plate": car.get("license_plate", "UNKNOWN"),
                "spot_id": car["spot_id"],
                "car_size": car.get("car_size", "unknown"),
                "checkin_time": car["checkin_time"].isoformat(),
                "floor": spot.get("floor", "unknown"),
                "bay": spot.get("bay", "unknown"),
                "spot_type": spot["type"],  # Guaranteed by $ifNull
                "spot_status": spot.get("status", "unknown")
            }

            # 4. Handle checkout data
            if car.get("checkout_time"):
                response.update({
                    "checkout_time": car["checkout_time"].isoformat() if car["checkout_time"] else None,
                    "fee": float(car.get("fee", 0))
                })
            else:
                response["current_duration_minutes"] = int(
                    (datetime.now() - car["checkin_time"]).total_seconds() / 60
                )

            return jsonify(response)

        except Exception as e:
            return jsonify({"error": f"System error: {str(e)}"}), 500