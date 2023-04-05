from fastapi import FastAPI, File, UploadFile
import pytesseract
import cv2
import numpy as np

app = FastAPI()

@app.post("/upload/")
async def upload_image(image: UploadFile = File(...)):
    img_array = np.frombuffer(await image.read(), dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # グレースケール変換 有効、精度多少向上
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 傾きの補正 ダメだった
    # img = deskew_image(img)

    # 画像のリサイズ あんまり効果ない？ほぼ変化なし
    # scale_factor = 2.0
    # new_width = int(img.shape[1] * scale_factor)
    # new_height = int(img.shape[0] * scale_factor)
    # img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    # ノイズ除去 ダメだった
    # img = cv2.medianBlur(img, 5)

    # 二値化 (Adaptive Thresholding) ダメだった
    # img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 12, 3)

    # 二値化 (Otsu's Binarization) ダメだった
    # _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # psm 6が一番良さそう、1～12まである
    text = pytesseract.image_to_string(img, lang='jpn', config='--psm 6 --oem 3')
    text_lines = text.split('\n')

    return {"text": text_lines}

def deskew_image(img):
    """
    !!没、あんまり効果なし
    画像の傾きを補正する
    """
    # Cannyエッジ検出を使用してエッジを検出
    edges = cv2.Canny(img, 50, 150, apertureSize=3)

    # Hough変換を使用して直線を検出
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)

    # 直線の角度を計算
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
        angles.append(angle)

    # 角度の中央値を計算して画像の回転角度を決定
    median_angle = np.median(angles)
    img_center = tuple(np.array(img.shape[1::-1]) / 2)
    rotation_matrix = cv2.getRotationMatrix2D(img_center, median_angle, 1.0)

    # 画像を回転させて傾きを補正
    img_rotated = cv2.warpAffine(img, rotation_matrix, img.shape[1::-1], flags=cv2.INTER_LINEAR)

    return img_rotated