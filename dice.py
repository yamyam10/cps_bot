from PIL import Image
import itertools
import os

# 6つの画像ファイルのパス
image_paths = [
    'dice/dice_1.png', 'dice/dice_2.png', 'dice/dice_3.png',
    'dice/dice_4.png', 'dice/dice_5.png', 'dice/dice_6.png'
]

# 画像を読み込む
images = [Image.open(image_path) for image_path in image_paths]

# 画像の名前を取得 (ファイル名の末尾の番号部分)
image_names = [os.path.splitext(os.path.basename(image_path))[0] for image_path in image_paths]

# 画像のサイズを取得
width, height = images[0].size

# 画像の並べ方（3つずつ横並びにする全通りの組み合わせ）
combinations = itertools.product(images, repeat=3)  # 3つずつの組み合わせ（重複あり）

# 結果を保存するディレクトリ（必要に応じて作成）
output_dir = 'output_images/'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 各組み合わせで画像を結合して保存
for idx, combo in enumerate(combinations):
    # 新しい画像の幅と高さを計算 (3つ横並びのサイズ)
    total_width = width * 3
    total_height = height

    # 新しい画像を作成
    new_image = Image.new('RGB', (total_width, total_height))

    # 画像を結合
    for i, image in enumerate(combo):
        x_offset = i * width
        new_image.paste(image, (x_offset, 0))

    # 画像ファイル名の組み合わせ（画像名を数字で連結）
    combo_names = ''.join([image_names[images.index(image)][-1] for image in combo])  # 画像名から番号部分を抽出
    file_name = f'{output_dir}dice_{combo_names}.jpg'
    
    # 結合した画像を保存
    new_image.save(file_name)

    print(f"Saved {file_name}")
