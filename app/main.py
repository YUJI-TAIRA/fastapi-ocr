from fastapi import FastAPI, File, UploadFile
import pytesseract
import cv2
import numpy as np
from requests.structures import CaseInsensitiveDict
from gyazo.api import Api
from gyazo.error import GyazoError
from gyazo.image import Image, ImageList
from time import sleep
from app.libs import trim
# os
import os
app = FastAPI()
client = Api(access_token=os.environ['GYAZO_ACCESS_TOKEN'])

@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    # cv2で画像を読み込み
    input_file = np.frombuffer(await file.read(), np.uint8)
    input_image = cv2.imdecode(input_file, cv2.IMREAD_COLOR)
    # グレースケールに変換
    gray_img = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    # 適応的閾値処理
    binary_img = cv2.adaptiveThreshold(
        compressed_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 255, 2
    )
    # ガウシアンフィルタで画像の平滑化
    size = (3, 3)
    blur = cv2.GaussianBlur(binary_img, size, 0)
    # 大津の手法を使った画像の２値化
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # # 白黒反転
    # th = cv2.bitwise_not(th)
    # # 大津の手法を使った画像の２値化
    # _, th = cv2.threshold(th, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # # 白黒反転で元に戻す
    # th = cv2.bitwise_not(th)

    # # サイズを500kbに圧縮
    image = compress_image_to_500kb(blur)
    # ファイルの形式を戻す
    image = cv2.imencode(".jpg", blur)[1].tobytes()
    

    # imgをgyazoにアップロード
    img = client.upload_image(image)
    sleep(8)
    test = client.get_image(image_id=img.image_id)
    # test.ocrがない場合はリトライ
    count = 0
    while test.ocr is None:
        sleep(4)
        test = client.get_image(image_id=img.image_id)
        # 3回リトライしてもダメならエラーを返す
        count += 1
        if count >= 3:
            return {"error": "OCR取得に失敗しました"}

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