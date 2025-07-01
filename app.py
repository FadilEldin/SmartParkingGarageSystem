from flask import Flask, render_template, request, jsonify
from models import Garage, get_db, SpotType
from services import ParkingService
import os
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)
db = get_db()

# Initialize garage
Garage.initialize()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/v1/api/spots', methods=['GET'])
def get_spots():
    try:
        # First get all spots
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

        # Then get additional car info for occupied spots
        occupied_spots = [s['spot_id'] for s in spots if s['status'] == 'occupied']
        cars = list(db.cars.find(
            {"spot_id": {"$in": occupied_spots}, "checkout_time": None},
            {"_id": 0, "license_plate": 1, "checkin_time": 1, "spot_id": 1}
        ))

        # Merge car info with spots
        car_map = {car['spot_id']: car for car in cars}
        for spot in spots:
            if spot['status'] == 'occupied' and spot['spot_id'] in car_map:
                duration = (datetime.now() - car_map[spot['spot_id']]['checkin_time']).total_seconds() / 60
                spot['license_plate'] = car_map[spot['spot_id']]['license_plate']
                spot['duration_minutes'] = int(duration)

        return jsonify(spots)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/v1/api/spots/available', methods=['GET'])
def get_available_spots():
    spot_type_str = request.args.get('type')
    spot_type = None
    if spot_type_str:
        try:
            spot_type = SpotType(spot_type_str)
        except ValueError:
            return jsonify({"error": f"Invalid spot type: {spot_type_str}"}), 400
    return ParkingService.get_available_spots(spot_type)

@app.route('/v1/api/cars/park', methods=['POST'])
def park_car():
    data = request.json
    return ParkingService.park_car(data['license_plate'], data['car_size'])

@app.route('/v1/api/cars/exit', methods=['POST'])
def exit_car():
    data = request.json
    return ParkingService.exit_car(data['license_plate'])

@app.route('/v1/api/cars/find', methods=['GET'])
def find_car():
    license_plate = request.args.get('license_plate')
    return ParkingService.find_car(license_plate)

@app.route('/oldfloor/<int:floor_number>')
def old_show_floor(floor_number):
    floor = db.floors.find_one({"floor_number": floor_number}, {"_id": 0})
    if not floor:
        return "Floor not found", 404
    return render_template('floor.html', floor=floor)


@app.route('/floor/<int:floor_number>')
def show_floor(floor_number):
    # Get floor data
    floor = db.floors.find_one({"floor_number": floor_number}, {"_id": 0})
    if not floor:
        return "Floor not found", 404

    # Get car information for occupied spots on this floor
    occupied_spots = []
    for bay in floor['bays']:
        for spot in bay['spots']:
            if spot['status'] == 'occupied':
                car = db.cars.find_one(
                    {"spot_id": spot['spot_id'], "checkout_time": None},
                    {"_id": 0, "license_plate": 1, "checkin_time": 1, "car_size": 1}
                )
                if car:
                    duration = int((datetime.now() - car['checkin_time']).total_seconds() / 60)
                    occupied_spots.append({
                        'spot_id': spot['spot_id'],
                        'license_plate': car['license_plate'],
                        'car_size': car['car_size'],
                        'duration_minutes': duration
                    })

    return render_template(
        'floor.html',
        floor=floor,
        occupied_spots={s['spot_id']: s for s in occupied_spots}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3333, debug=True)