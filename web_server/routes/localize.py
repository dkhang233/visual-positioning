import os
import uuid

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

localize_router = APIRouter(prefix="/localize")


# Lấy ảnh từ client và lưu vào thư mục
@localize_router.post("/image")
def init_localization():
    return "ok"


# Trả về thông tin pose cho client
@localize_router.get("/pose")
def init_localization():
    # Giả sử bạn đã có một pose nào đó để trả về
    pose = {
        "x": 1.0,
        "y": 2.0,
        "z": 3.0,
        "rotation": {
            "roll": 0.1,
            "pitch": 0.2,
            "yaw": 0.3
        }
    }
    return jsonable_encoder(pose)

#update vị trí trong 10s
def update_location(duration_secondss = 10):
    for i in range(duration_seconds):
        jsonable_encoder()
        time.sleep(1)














# Xác định bản đồ + vị trí
@localize_router.post("/init")
def init_localization(name: str, request):
    return jsonable_encoder("haha")

# Xác định vị trí khi di chuyển trong bản đồ
@localize_router.post("{name}/navigate")
def navigate(name: str, request):
    # Download an image, save it and localize it against the map
    image = request.files["image"]

    # Create the folder if it doesn't exist
    random_id = str(uuid.uuid4())
    folder_path = os.path.join("data", "query_data", name, str(random_id))
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Save the uploaded image
    image_path = os.path.join(folder_path, "query_image.png")
    image.save(image_path)

    # Call the localization function
    # pose = localizer.localize(image_path, name)
    # print("Localizer Result: ", pose)
    pose = {
        "status": "success",
        "message": "Image localized successfully",
        "image_path": image_path,
        "map_name": name,
        "pose": {
            "x": 1.0,
            "y": 2.0,
            "z": 3.0,
            "rotation": {
                "roll": 0.1,
                "pitch": 0.2,
                "yaw": 0.3
            }
        }
    }
    return jsonable_encoder(pose)