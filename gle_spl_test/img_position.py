from PIL import Image, ImageDraw

# 画像を開く
image_path = 'gle_spl_test/test.png'
image = Image.open(image_path)

# 描画オブジェクトを作成
draw = ImageDraw.Draw(image)

# 項目の位置を矩形で描画（例: 名前、スコア、キルの位置）
# (左, 上, 右, 下)
name_region = (240, 1020, 600, 1730)
score_region = (270, 660, 870, 860)
kills_region = (940, 1020, 1075, 1730)

# 領域を矩形で描画
draw.rectangle(name_region, outline="red")
draw.rectangle(score_region, outline="green")
draw.rectangle(kills_region, outline="blue")

# 結果の画像を保存
output_path = 'output2.png'
image.save(output_path)

# 結果の画像を表示（任意）
image.show()
