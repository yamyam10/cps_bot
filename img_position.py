from PIL import Image, ImageDraw

# 画像を開く
image_path = 'test.png'
image = Image.open(image_path)

# 描画オブジェクトを作成
draw = ImageDraw.Draw(image)

# 項目の位置を矩形で描画（例: 名前、スコア、キルの位置）
name_region = (50, 100, 300, 150)
score_region = (350, 100, 450, 150)
kills_region = (500, 100, 600, 150)

# 領域を矩形で描画
draw.rectangle(name_region, outline="red")
draw.rectangle(score_region, outline="green")
draw.rectangle(kills_region, outline="blue")

# 結果の画像を保存
output_path = 'output.png'
image.save(output_path)

# 結果の画像を表示（任意）
image.show()
