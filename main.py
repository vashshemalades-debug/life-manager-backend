from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import date, datetime, timedelta
from typing import List

app = FastAPI()

# CORS ruxsatnomalari
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MONGODB ULANIŞI ---
# O'zingiz tayyorlagan parolli kodni shu yerga qo'ying:
MONGO_URL = "mongodb+srv://vashshemalades_db_user:sherbek15147051@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority"
client = AsyncIOMotorClient(MONGO_URL)
db = client.hayot_menejeri  # Baza nomi

# --- MODELLAR ---
class Xarajat(BaseModel):
    nomi: str
    narxi: int

class Vazifa(BaseModel):
    matn: str

# MongoDB ID'larini frontendga moslab o'zgartirish (Yordamchi funksiya)
def fix_id(item):
    item["id"] = str(item["_id"])
    del item["_id"]
    return item

# --- ANALITIKA ---
@app.get("/statistika")
async def get_statistika():
    bugun = date.today().isoformat()
    hafta_boshi = (datetime.now() - timedelta(days=7)).date().isoformat()
    oy_boshi = date.today().replace(day=1).isoformat()

    # Statistika uchun barcha xarajatlarni olish
    cursor = db.xarajatlar.find()
    bugun_sum = 0
    hafta_sum = 0
    oy_sum = 0

    async for item in cursor:
        sana = item.get("sana")
        narxi = item.get("narxi", 0)
        if sana == bugun: bugun_sum += narxi
        if sana >= hafta_boshi: hafta_sum += narxi
        if sana >= oy_boshi: oy_sum += narxi

    return {
        "bugun": bugun_sum,
        "hafta": hafta_sum,
        "oy": oy_sum
    }

# --- XARAJATLAR ---
@app.get("/xarajatlar")
async def get_xarajatlar():
    cursor = db.xarajatlar.find().sort("sana", -1)
    return [fix_id(item) async for item in cursor]

@app.post("/xarajatlar")
async def add_expense(item: Xarajat):
    new_expense = {
        "nomi": item.nomi,
        "narxi": item.narxi,
        "sana": date.today().isoformat()
    }
    await db.xarajatlar.insert_one(new_expense)
    return {"status": "ok"}

@app.delete("/xarajatlar/{item_id}")
async def delete_expense(item_id: str):
    await db.xarajatlar.delete_one({"_id": ObjectId(item_id)})
    return {"status": "deleted"}

# --- VAZIFALAR ---
@app.get("/vazifalar")
async def get_tasks():
    cursor = db.vazifalar.find().sort("_id", -1)
    return [fix_id(item) async for item in cursor]

@app.post("/vazifalar")
async def add_task(item: Vazifa):
    new_task = {"matn": item.matn, "holat": False}
    await db.vazifalar.insert_one(new_task)
    return {"status": "ok"}

@app.delete("/vazifalar/{task_id}")
async def delete_task(task_id: str):
    await db.vazifalar.delete_one({"_id": ObjectId(task_id)})
    return {"status": "deleted"}

@app.put("/vazifalar/{task_id}")
async def update_task(task_id: str):
    task = await db.vazifalar.find_one({"_id": ObjectId(task_id)})
    if task:
        new_status = not task.get("holat", False)
        await db.vazifalar.update_one({"_id": ObjectId(task_id)}, {"$set": {"holat": new_status}})
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)