from datetime import datetime
from enum import Enum
from pymongo import MongoClient
import os

# Initialize MongoDB connection
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client.parking_garage

def get_db():
    return db


class SpotType(Enum):
    COMPACT = "compact"
    STANDARD = "standard"
    OVERSIZED = "oversized"
    EV_CHARGING = "ev_charging"

    @property
    def compatible_sizes(self):
        return {
            SpotType.COMPACT: [CarSize.SMALL],
            SpotType.STANDARD: [CarSize.SMALL, CarSize.MEDIUM],
            SpotType.OVERSIZED: [CarSize.SMALL, CarSize.MEDIUM, CarSize.LARGE],
            SpotType.EV_CHARGING: [CarSize.SMALL, CarSize.MEDIUM]  # Assuming EV spots are standard size
        }[self]


class CarSize(Enum):
    SMALL = "small"  # Fits in compact, standard, oversized
    MEDIUM = "medium"  # Fits in standard, oversized
    LARGE = "large"  # Fits only in oversized

# MongoDB connection
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client.parking_garage


class Garage:
    @staticmethod
    def initialize():
        if db.floors.count_documents({}) == 0:
            # Sample garage with 2 floors, 3 bays each, 20 total spots
            floors = [
                {
                    "floor_number": 1,
                    "bays": [
                        {
                            "bay_id": "A",
                            "spots": [
                                {"spot_id": f"1-A-{i}", "type": SpotType.STANDARD.value,
                                 "status": "available"} for i in range(1, 6)
                            ]
                        },
                        {
                            "bay_id": "B",
                            "spots": [
                                {"spot_id": f"1-B-{i}", "type": SpotType.COMPACT.value,
                                 "status": "available"} for i in range(1, 6)
                            ]
                        }
                    ]
                },
                {
                    "floor_number": 2,
                    "bays": [
                        {
                            "bay_id": "C",
                            "spots": [
                                {"spot_id": f"2-C-{i}", "type": SpotType.EV_CHARGING.value,
                                 "status": "available"} for i in range(1, 6)
                            ]
                        },
                        {
                            "bay_id": "D",
                            "spots": [
                                {"spot_id": f"2-D-{i}", "type": SpotType.OVERSIZED.value,
                                 "status": "available"} for i in range(1, 6)
                            ]
                        }
                    ]
                }
            ]
            db.floors.insert_many(floors)


class ParkingSpot:
    @staticmethod
    def find_available(spot_type=None):
        query = {"status": "available"}
        if spot_type:
            query["type"] = spot_type.value
        return db.floors.aggregate([
            {"$unwind": "$bays"},
            {"$unwind": "$bays.spots"},
            {"$match": {"bays.spots.status": "available"}},
            {"$project": {
                "_id":0,
                "floor": "$floor_number",
                "bay": "$bays.bay_id",
                "spot_id": "$bays.spots.spot_id",
                "type": "$bays.spots.type",
                "status": "$bays.spots.status"
            }}
        ])


class Car:
    @staticmethod
    def check_in(license_plate, spot_id, car_size):
        checkin_time = datetime.now()
        car_data = {
            "license_plate": license_plate,
            "spot_id": spot_id,
            "car_size": car_size.value,
            "checkin_time": checkin_time,
            "checkout_time": None,
            "fee": 0
        }
        db.cars.insert_one(car_data)

        # Update spot status
        db.floors.update_one(
            {"bays.spots.spot_id": spot_id},
            {"$set": {"bays.$[].spots.$[spot].status": "occupied"}},
            array_filters=[{"spot.spot_id": spot_id}]
        )
        return car_data

    @staticmethod
    def check_out(license_plate):
        car = db.cars.find_one({"license_plate": license_plate, "checkout_time": None})
        if not car:
            return None

        checkout_time = datetime.now()
        duration_seconds = int((checkout_time - car["checkin_time"]).total_seconds())
        duration = duration_seconds / 3600  # hours

        # Calculate fee based on spot type and duration
        spot = db.floors.aggregate([
            {"$unwind": "$bays"},
            {"$unwind": "$bays.spots"},
            {"$match": {"bays.spots.spot_id": car["spot_id"]}},
            {"$limit": 1}
        ]).next()

        spot_type = spot["bays"]["spots"]["type"]
        hourly_rates = {
            SpotType.COMPACT.value: 5,
            SpotType.STANDARD.value: 7,
            SpotType.OVERSIZED.value: 10,
            SpotType.EV_CHARGING.value: 8
        }
        rate = hourly_rates.get(spot_type, 7)
        fee = rate * duration

        # Update car record
        db.cars.update_one(
            {"_id": car["_id"]},
            {"$set": {"checkout_time": checkout_time, "fee": round(fee, 2)}}
        )

        # Update spot status
        db.floors.update_one(
            {"bays.spots.spot_id": car["spot_id"]},
            {"$set": {"bays.$[].spots.$[spot].status": "available"}},
            array_filters=[{"spot.spot_id": car["spot_id"]}]
        )

        calculation = f"${rate:.2f} x {duration:.2f} hours = ${fee:.2f} ({spot_type} spot)"

        return {
            "license_plate": license_plate,
            "duration_hours": round(duration, 2),
            "duration_seconds": duration_seconds,
            "fee": round(fee, 2),
            "spot_type": spot_type,
            "rate": rate,
            "calculation": calculation
        }