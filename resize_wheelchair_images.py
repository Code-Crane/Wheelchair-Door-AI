import os
from PIL import Image

# 경로 설정
input_dir = './dataset/wheelchair_raw'
output_dir = './dataset/wheelchair_resized'
os.makedirs(output_dir, exist_ok=True)

# 리사이즈 크기 설정
resize_to = (224, 224)

# 이미지 순회
count = 0
for filename in os.listdir(input_dir):
    input_path = os.path.join(input_dir, filename)
    output_path = os.path.join(output_dir, filename)
    try:
        with Image.open(input_path) as img:
            resized = img.convert('RGB').resize(resize_to, Image.LANCZOS)
            resized.save(output_path)
            count += 1
            print(f"[{count}] 리사이징 완료 → {filename}")
    except Exception as e:
        print(f"⚠️ 오류: {filename} → {e}")

print(f"\n✅ 총 {count}장 리사이징 완료! 저장 위치: {output_dir}")
