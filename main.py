from datetime import date

from fastapi import FastAPI, HTTPException, status
import uvicorn

from database import Base, engine
import models

from pydantic import BaseModel, Field
from typing import List

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Interview Shipmnts",
    version="1.0.0"
)

ships_db = {}
voyage_db = {}
containers_db = {}

@app.get("/")
def health_check():
    return {"message" : "API is running"}

#API1
class ShipCreate(BaseModel):
    name: str = Field(..., examples=["MV Example"])
    vessel_number: str = Field(..., examples=["VS001"])
    capacity: int = Field(..., gt=0, description="Container capacity", examples=[3])


class ShipResponse(BaseModel):
    id: str
    name: str
    vessel_number: str
    capacity: int

@app.post("/vessels",
          response_model = ShipResponse,
          status_code=status.HTTP_201_CREATED,
          summary = "Register a new ship"
)

async def Register_Ship(ship_data: ShipCreate):
    for ship in ships_db.values():
        if ship["vessel_number"] == ship_data.vessel_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vessel number '{ship_data.vessel_number}' is already registered."
            )
    next_id = f"v{len(ships_db) + 1}"

    new_ship = {
        "id": next_id,
        "name": ship_data.name,
        "vessel_number": ship_data.vessel_number,
        "capacity": ship_data.capacity,
    }

    ships_db[next_id] = new_ship

    return new_ship


#API2
class CreateVoyage(BaseModel):
    vessel_id: str = Field(..., examples=["v1"])
    voyage_number: str = Field(..., examples=["V001"])
    destination: str = Field(..., examples=["Singapore"])

class VoyageResponse(BaseModel):
    id: str
    vessel_id: str
    voyage_number:str
    destination: str
    status: str
    effective_route: List

@app.post("/voyages",
          response_model = VoyageResponse,
          status_code=status.HTTP_201_CREATED,
          summary = "Created a new Voyage")

def start_voyage(payload: CreateVoyage):
    for voyage in voyage_db:
        if voyage["voyage_number"] == payload.voyage_number:
            raise HTTPException(
                status_code=400, 
                detail="voyage_number already exists"
            )
        
    next_id = f"v{len(voyage_db) + 1}"

    new_voyage = {
        "id": next_id,
        "vessel_id": payload.vessel_id,
        "voyage_number": payload.voyage_number,
        "destination": payload.destination,
        "status": "PLANNED",
        "effective_route" : []
    }

    voyage_db[next_id] = new_voyage
    return new_voyage


#API3
class AddContainer(BaseModel):
    container_number: str = Field(..., examples=["C001"])
    destination: str = Field(..., examples=["Dubai"])
    due_date: date = Field(..., examples=["2026-08-20"])
    late_charge: int = Field(..., gt=0, examples=[500])

class AddContainerResponse(BaseModel):
    id: str
    container_number: str
    voyage_id: str
    destination: str
    due_date: date
    late_charge: int
    arrived_on: str

@app.post("/voyages/{voyage_id}/containers",
          response_model = AddContainerResponse,
          status_code=status.HTTP_201_CREATED,
          summary = "Added a container to a existing voyage")

async def load_container(voyage_id: str, payload: AddContainer):
     if voyage_id not in voyage_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No voyage found with id {voyage_id}"
        )

     voyage = voyage_db[voyage_id]
     vessel = ships_db[voyage_db["vessel_id"]]


     for c in containers_db.values():
         if c["container_number"] == payload.container_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"CONTAINER_ALREADY_EXISTS"
            )

         if voyage["status"] != "PLANNED":
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"VOYAGE_ALREADY_STARTED"
            )

         current_load = sum(1 for c in containers_db.values() if c["voyage_id"] == voyage_id)
         if current_load >= vessel["capacity"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"CAPACITY_EXCEEDED: {vessel['name']} can carry only {vessel['capacity']} containers on one voyage"
            )

         new_id = f"c{len(containers_db) + 1}"

         new_container = {
             "id": new_id,
             "container_number": payload.container_number,
             "voyage_id": voyage_id,
             "destination": payload.destination,
             "due_date": payload.due_date,
             "late_charge": payload.late_charge,
             "arrived_on": None
         }

         containers_db[new_id] = new_container
         return new_container


# #API4
# class AddHop(BaseModel):
#       from_field: str = Field(..., alias="from")
#       to: str = Field(..., examples=["Dubai"])
#       reached_on: date = Field(..., examples=["2026-08-23"])

# class AddHopRequest(BaseModel):
#     id: str
#     voyage_id: str
#     from_field : str
#     to: str
#     reached_on: date
#     voyage_status: str
#     effective_route: list
#     arrived_containers: dict

# @app.post("/voyages/{voyage_id}/hops",
#           response_model = AddHop,
#           status_code=status.HTTP_201_CREATED,
#           summary = "Added a hop to a existing voyage")

# async def add_hop_to_voyage(voyage_id: str, hop_data: AddHop):

#     if voyage_id not in voyage_db:
#          raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"VOYAGE_NOT_FOUND"
#          )

#     voyage = voyage_db[voyage_id]
#     route = voyage.setdefault("effective_route", [])
#     route.append(hop_data.to_place)

#     hop_id = f"h{len(voyage_db.get('hops', [])) + 1}"
#     new_hop = {
#         "id": hop_id,
#         "voyage_id": voyage_id,
#         "from": hop_data.from_place,
#         "to": hop_data.to_place,
#         "reached_on": hop_data.reached_on,
#         "voyage_status": voyage_db["voyage_status"],
#         "effective_route": route,
#     }
    
#     voyage_db.setdefault("hops", []).append(new_hop)
#     return new_hop


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
