from fastapi import FastAPI, File, UploadFile
import pytesseract
import cv2
import numpy as np
from requests.structures import CaseInsensitiveDict
from gyazo.api import Api
from gyazo.error import GyazoError
from gyazo.image import Image, ImageList
from time import sleep
# os
import os
app = FastAPI()
client = Api(access_token=os.environ['GYAZO_ACCESS_TOKEN'])

@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    # HEICをJPGに変換

    image = await file.read()
    # グレースケール変換
    image = cv2.imdecode(np.frombuffer(image, np.uint8), 0)
    # # サイズを500kbに圧縮
    image = compress_image_to_500kb(image)
    # # ファイルの形式を戻す
    image = cv2.imencode(".jpg", image)[1].tobytes()
    

    # imgをgyazoにアップロード
    img = client.upload_image(image)
    sleep(8)
    test = client.get_image(image_id=img.image_id)
    # test.ocrがない場合はリトライ
    while test.ocr is None:
        sleep(4)
        test = client.get_image(image_id=img.image_id)

    # imgのocrを取得
    print(test.ocr)

    # ocrを改行して整形
    ocr = test.ocr["description"].splitlines()

    return {"img_id": test.image_id, "ocr": ocr} 


def compress_image_to_500kb(image: np.ndarray) -> np.ndarray:
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    result, enc_img = cv2.imencode('.jpg', image, encode_param)

    # Check if the compressed image size is less than or equal to 500KB
    while enc_img.nbytes > 500 * 1024:
        encode_param[1] -= 5  # Reduce the quality by 5
        result, enc_img = cv2.imencode('.jpg', image, encode_param)

    # Decode the compressed image back to a numpy array
    compressed_image = cv2.imdecode(enc_img, cv2.IMREAD_UNCHANGED)
    
    return compressed_image