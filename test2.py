import discord
import os
from discord import app_commands
from discord.ext import commands
import random
from dotenv import load_dotenv

class HeroRoulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.heroes = [
            {"id": 1, "name": "十文字 アタリ", "color": 0xfa3d2a, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079589000899215510/atari.jpg"},
            {"id": 2, "name": "ジャスティス ハンコック", "color": 0x2854a6, "type": "オリジナル", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079591675237765151/BA95BD5E-6BBB-4595-895D-E8899B274F8C.jpg"},
            {"id": 3, "name": "リリカ", "color": 0xf33d8e, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079592519316283402/976856A4-E9DB-47E8-AB0C-3577E11C8874.jpg"},
            {"id": 4, "name": "双挽 乃保", "color": 0xa2009e, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079592519794442240/A12A575D-6ED1-48D5-ACFA-D73CF3777673.jpg"},
            {"id": 5, "name": "桜華 忠臣", "color": 0x92d400, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079592520176107540/BBC71FFC-3B20-42A6-984C-E6A0A7B29B61.jpg"},
            {"id": 6, "name": "ジャンヌ ダルク", "color": 0xae9100, "type": "オリジナル", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079592520503271484/38456329-3174-4B6A-92F4-4224617E701F.jpg"},
            {"id": 7, "name": "マルコス'55", "color": 0xa66400, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079595693527805983/FACDB93C-0161-47C9-BE73-A2B2A6385F16.jpg"},
            {"id": 8, "name": "ルチアーノ", "color": 0x323f3e, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079595755431538708/3D8ECCD0-BACB-4FB7-A25A-94ED406181CC.jpg"},
            {"id": 9, "name": "Voidoll", "color": 0x002ea2, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079595767561470093/102C116C-532D-487A-8713-13D695E296E1.jpg"},
            {"id": 10, "name": "深川 まとい", "color": 0xd5281d, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079595777791369296/34143245-6B32-4CE8-8CFE-EC94C519BFC9.jpg"},
            {"id": 11, "name": "グスタフ ハイドリヒ", "color": 0x4d2275, "type": "オリジナル", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079596135842324500/14571E65-24EF-4794-8C21-680F7BC4E65B.jpg"},
            {"id": 12, "name": "ニコラ テスラ", "color": 0xf6c230, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079596200996655214/A7A96801-215D-492A-9CDF-99D6C21EFC29.jpg"},
            {"id": 13, "name": "ヴィオレッタ ノワール", "color": 0x554230, "type": "オリジナル", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079596490978246706/07D8826E-C841-42A8-9DA1-588E499F4247.jpg"},
            {"id": 14, "name": "コクリコット ブランシュ", "color": 0x33b5b2, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079596685136777247/3686F67D-5A3A-4BC2-8B25-CD344C6A17D5.jpg"},
            {"id": 15, "name": "マリア=S=レオンブルク", "color": 0x61001f, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079597242719154246/53F87257-5954-4158-B45D-29244216DBF4.jpg"},
            {"id": 16, "name": "アダム=ユーリエフ", "color": 0x3295b6, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079597086842028044/038D0708-B29D-4FE4-9B8F-CBC3FA4B419B.jpg"},
            {"id": 17, "name": "13†サーティーン†", "color": 0x121212, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079598471520206958/41295EA9-09D7-4C51-A200-B93E3961BB71.jpg"},
            {"id": 18, "name": "かけだし勇者", "color": 0x4148d8, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079598665141866537/B05EA783-5599-4C0E-BB4E-8FD721868490.jpg"},
            {"id": 19, "name": "メグメグ", "color": 0xfca3b7, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079598919882899526/56D4234A-3539-45A2-BE82-21C416E38E22.jpg"},
            {"id": 20, "name": "イスタカ", "color": 0xc56b4a, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079599439955628153/AD67E48A-B185-46F6-8B5D-59F27D9EB9F9.jpg"},
            {"id": 21, "name": "輝龍院 きらら", "color": 0xa60200, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079599695522967552/77F10B37-107E-4E5A-9771-BE7B898F73F3.jpg"},
            {"id": 22, "name": "ヴィーナス ポロロッチョ", "color": 0x504040, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079600163171074139/57F081B3-96A5-4754-B855-53B27A759426.jpg"},
            {"id": 23, "name": "ソーン=ユーリエフ", "color": 0xcbc7c3, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079600174587969606/7A9EF4DF-8868-42E7-8D3E-C0CDC80BD789.jpg"},
            {"id": 24, "name": "デビルミント鬼龍 デルミン", "color": 0xbd9bf0, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079600185958731836/5DC7B221-9E48-4827-96C0-65E7B9BC9516.jpg"},
            {"id": 25, "name": "トマス", "color": 0x7596bf, "type": "オリジナル", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079600198021550120/FAE82E6F-EBC7-43A2-A696-5EB25F87F1FC.jpg"},
            {"id": 26, "name": "零夜", "color": 0xcfff00, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079601008646295562/170A967F-906B-4627-B183-1F391F225E3C.jpg"},
            {"id": 27, "name": "ルルカ", "color": 0xff8b18, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079601022823051274/92E07745-0A38-4C41-91F5-9BEA36AE3F10.jpg"},
            {"id": 28, "name": "ピエール 77世", "color": 0xae78da, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079601037830258699/59B863FF-AC8F-4CC0-9A8D-5B04A2D1772E.jpg"},
            {"id": 29, "name": "狐ヶ咲 甘色", "color": 0xa887a8, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079601051902148618/E5FE6584-B68F-4E09-A7ED-B114C5ED9BEF.jpg"},
            {"id": 30, "name": "HM-WA100 ニーズヘッグ", "color": 0x9a0404, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079601064875134996/34375C22-971D-41D0-A684-A34A548EFE4E.jpg"},
            {"id": 31, "name": "ゲームバズーカガール", "color": 0x65a3de, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079601912149708881/74304C6F-F6CA-41FB-9965-D74ED35B6313.jpg"},
            {"id": 32, "name": "青春 アリス", "color": 0x65a3de, "type": "オリジナル", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079601960979792002/435D51B5-2C5C-4BC7-8671-A16B4A4A5C84.jpg"},
            {"id": 33, "name": "イグニス=ウィル=ウィスプ", "color": 0xe35479, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079602285946093578/AD86981E-94B1-4774-AAE7-5416E12875C1.jpg"},
            {"id": 34, "name": "糸廻 輪廻", "color": 0x817a8d, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079601997046632548/5167C0AA-6D15-4BB9-80D4-EC0C9EE6C0D2.jpg"},
            {"id": 35, "name": "Bugdoll", "color": 0x132832, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079602677048156242/38D6EF6C-8DE4-4A44-9E4B-87423F860554.jpg"},
            {"id": 36, "name": "ステリア・ララ・シルワ", "color": 0x00956d, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079602677362737152/D72FBFEB-CE47-4072-B596-2A09C1280354.jpg"},
            {"id": 37, "name": "ラヴィ・シュシュマルシュ", "color": 0xf75096, "type": "オリジナル", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079602677677314098/932678DD-F687-40CD-8441-4C033EB378C5.jpg"},
            {"id": 38, "name": "アル・ダハブ=アルカティア", "color": 0xa239b7, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1079602677928960010/D6E27199-0E19-4637-A1D7-90B9A95FA24D.jpg"},
            {"id": 39, "name": "天空王 ぶれいずどらごん", "color": 0xA597E2, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1121659070395461703/0C97927B-6B91-41A8-AAB5-2810CE7DA9B2.jpg"},
            {"id": 40, "name": "某 <なにがし>", "color": 0x000000, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1248323586851078154/3C684963-E0AD-4C36-8A95-83DFEE35A1B0.jpg"},
            {"id": 41, "name": "クー・シー", "color": 0xfff300, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1248323587299872990/0A3BA2FA-763E-4596-947E-A633D689B931.jpg"},
            {"id": 42, "name": "アミスター=バランディン", "color": 0x61001f, "type": "オリジナル", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1248323587501195336/012C8FBA-B957-40F2-B5A3-7750B3182102.jpg"},
            {"id": 43, "name": "ソル=バッドガイ", "color": 0x990c02, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081092479538962483/FF21B5E4-DE3A-430D-896D-8F4D3B7CF769.jpg"},
            {"id": 44, "name": "ディズィー", "color": 0x3acd5c, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081092479778029589/6EF61A45-2A9B-45D1-92DC-F5D5A4F9720A.jpg"},
            {"id": 45, "name": "リュウ", "color": 0xaf4400, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081093082172366888/6F30A250-5D32-4A08-ABE4-37129EB1A2E2.jpg"},
            {"id": 46, "name": "春麗", "color": 0x0086a9, "type": "コラボ", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081093082382090301/E1F5305C-974F-42E1-B917-408060CE5A23.jpg"},
            {"id": 47, "name": "エミリア", "color": 0x8e60aa, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081094398319792138/6E39E36C-5077-4922-A4CC-6908930B74ED.jpg"},
            {"id": 48, "name": "レム", "color": 0x5181c7, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081094398500151337/3DBF1716-A368-444D-8999-B5504760986D.jpg"},
            {"id": 49, "name": "カイ=キスク", "color": 0x283e69, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081095042615234660/7163B2DF-A787-4F4F-8D00-E044B3D1958E.jpg"},
            {"id": 50, "name": "鏡音 リン", "color": 0xe2e27c, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081095136865431602/02D98176-0F1E-40D9-B160-988E8846F71C.jpg"},
            {"id": 51, "name": "鏡音 レン", "color": 0xe2e27c, "type": "コラボ", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081095137096110100/2568DC7F-CDCB-4988-BDD7-1A69C0558788.jpg"},
            {"id": 52, "name": "ザック＆レイチェル", "color": 0x330a0a, "type": "コラボ", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081095284475576390/B9CC908C-9CD2-48EC-9EA8-71CED671BA60.jpg"},
            {"id": 53, "name": "モノクマ", "color": 0x000000, "type": "コラボ", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081095284760784906/782A56F7-F2EF-430E-B390-EC290CC594C9.jpg"},
            {"id": 54, "name": "アクア", "color": 0x75c8e0, "type": "コラボ", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081095938963156992/79785A83-792A-45DC-866F-1163244A5904.jpg"},
            {"id": 55, "name": "めぐみん", "color": 0xc74438, "type": "コラボ", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081095939164471366/5625D206-69F3-493C-BA9B-915CBA01B497.jpg"},
            {"id": 56, "name": "リヴァイ", "color": 0xb3a379, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081096059671035904/7A829830-C950-4266-B1EF-E9F7996A3B18.jpg"},
            {"id": 57, "name": "猫宮 ひなた", "color": 0xf97d00, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081096059926884373/DDDB002F-ED28-4A91-AFA9-581B8599AB81.jpg"},
            {"id": 58, "name": "岡部 倫太郎", "color": 0xff9600, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081096076817346611/8113B66F-F1BC-4554-9E8E-57ECE0AF622A.jpg"},
            {"id": 59, "name": "セイバーオルタ", "color": 0x202130, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081096784446763128/16A1F7A9-A1D9-4B42-8A14-F19416A2A727.jpg"},
            {"id": 60, "name": "ギルガメッシュ", "color": 0xe3b100, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081096784673243177/9692E191-C827-4265-815E-268CB318A71C.jpg"},
            {"id": 61, "name": "佐藤四郎兵衛忠信", "color": 0xfbd3d3, "type": "コラボ", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081096945709359104/18EB4604-EB18-475B-BA0A-0D1E1EB2E6C0.jpg"},
            {"id": 62, "name": "アイズ・ヴァレンシュタイン", "color": 0x5871bb, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081096945952636968/F80B078B-751A-49EE-B766-28B674DF14DC.jpg"},
            {"id": 63, "name": "ノクティス", "color": 0x969da2, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081096946162339870/BAAD2116-C89E-40E0-92B3-3A4CDACD4082.jpg"},
            {"id": 64, "name": "中島 敦", "color": 0x9d9d94, "type": "コラボ", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081097631780053094/541800CF-E82B-4558-ABC5-AC2653269988.jpg"},
            {"id": 65, "name": "芥川 龍之介", "color": 0x675f6d, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081097631993954355/D85C2F03-8BC6-445A-83A0-7EA934AB4423.jpg"},
            {"id": 66, "name": "ライザリン・シュタウト", "color": 0xe7c559, "type": "コラボ", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081097771899166780/F2A0CC43-5007-4EE9-A15F-794499654D16.jpg"},
            {"id": 67, "name": "ジョーカー", "color": 0xe02323, "type": "コラボ", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081097772163403886/07B5032A-66A4-4DD0-8E79-2368F41E2DE2.jpg"},
            {"id": 68, "name": "アインズ・ウール・ゴウン", "color": 0x302e38, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081098716737458236/832C33BD-3880-48AB-B407-5EA0166C867F.jpg"},
            {"id": 69, "name": "キリト", "color": 0x9e9b9a, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081098716976517121/2532B52B-3495-4B3A-9AB5-4B239147EF83.jpg"},
            {"id": 70, "name": "アスナ", "color": 0xe9e9f1, "type": "コラボ", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081098851496243310/83B3BD0C-7064-40BD-AA60-7F4F71CC4CE3.jpg"},
            {"id": 71, "name": "ラム", "color": 0xd35d86, "type": "コラボ", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081098851710160986/B9120F36-8131-4444-B4E6-82DC0A170A35.jpg"},
            {"id": 72, "name": "2B", "color": 0xb2af9a, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081098974649393172/434F0391-7A64-45CA-AAF3-3DC4CD8E6BE5.jpg"},
            {"id": 73, "name": "リムル=テンペスト", "color": 0x5db0cf, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081098974871699476/C9AB6B72-EEAA-40F2-AB97-72FA4959C40A.jpg"},
            {"id": 74, "name": "御坂 美琴", "color": 0xffc155, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081099102395310172/463C6689-A955-4112-AC17-A5913C1D9346.jpg"},
            {"id": 75, "name": "アクセラレータ", "color": 0x8e95a6, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081099102613418004/3762CDA0-E252-4726-BC79-90903CCEB20E.jpg"},
            {"id": 76, "name": "ベル・クラネル", "color": 0x5177a2, "type": "コラボ", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1121661538831446066/F10806AC-75BA-4B47-B4B7-B1B76B4075C7.jpg"},
            {"id": 77, "name": "ロキシー・ミグルディア", "color": 0xbfcaf7, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1121661547157139467/D6E33CE6-FF8C-4BA7-9B48-95B93EACBC4D.jpg"},
            {"id": 78, "name": "ロックマン.EXE & 光熱斗", "color": 0x47c2f4, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1248333509857251358/0CF46AF0-FEA1-4930-93FB-BAB2DD3B1F0E.jpg"},
            {"id": 79, "name": "デンジ", "color": 0xffd734, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1248333510159110204/B202C319-F7FA-42AF-8711-544CDE0D1A3F.jpg"},
            {"id": 80, "name": "パワー", "color": 0xe76455, "type": "コラボ", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1248333510381666414/CD2FA0E7-52DC-4A11-9D26-4554811DD781.jpg"},
            {"id": 81, "name": "シノン", "color": 0x18989b, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1248333510595444776/0770644E-F05E-49A8-A8C2-59F8F929498E.jpg"},
            {"id": 82, "name": "ターニャ・デグレチャフ", "color": 0x47574f, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1248333510805028915/37139A0F-1D30-4EF4-9A02-C42240080BBF.jpg"}
        ]
        self.reset_settings()

    def reset_settings(self):
        self.selected_roles = {"アタッカー", "スプリンター", "ガンナー", "タンク"}
        self.selected_types = {"オリジナル", "コラボ"}

    def filter_heroes(self):
        return [
            hero for hero in self.heroes
            if hero["role"] in self.selected_roles and hero["type"] in self.selected_types
        ]

    def get_embed_hero(self, hero):
        embed = discord.Embed(title="", color=hero["color"])
        embed.set_author(name=hero["name"], icon_url=hero["img"])
        return embed

    @app_commands.command(name="ルーレット設定", description="ヒーロールーレット設定")
    async def setup_roulette(self, interaction: discord.Interaction):
        await interaction.response.send_message("ルーレット設定", view=RouletteSettingsView(self), ephemeral=True)

    @app_commands.command(name="ヒーロー", description="ランダムでヒーローを表示")
    async def random_hero_command(self, interaction: discord.Interaction):
        await self.random_hero(interaction)

    async def random_hero(self, interaction: discord.Interaction):
        filtered_heroes = self.filter_heroes()
        if not filtered_heroes:
            await interaction.response.send_message("条件に合うヒーローがいません。")
            return
        hero = random.choice(filtered_heroes)
        embed = self.get_embed_hero(hero)
        await interaction.response.send_message(embed=embed)

class RouletteSettingsView(discord.ui.View):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        self.update_buttons()

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji=":at:1249625709517733941")
    async def attacker(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle_setting("アタッカー", button)
        await self.update_message(interaction)

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji=":sp:1249625777235034195")
    async def sprinter(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle_setting("スプリンター", button)
        await self.update_message(interaction)

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji=":gn:1249625749854490686")
    async def gunner(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle_setting("ガンナー", button)
        await self.update_message(interaction)

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji=":tn:1249625807836414002")
    async def tank(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle_setting("タンク", button)
        await self.update_message(interaction)

    @discord.ui.button(label="オリジナル", style=discord.ButtonStyle.primary, row=1)
    async def original(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle_setting("オリジナル", button)
        await self.update_message(interaction)

    @discord.ui.button(label="コラボ", style=discord.ButtonStyle.primary, row=1)
    async def collaboration(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle_setting("コラボ", button)
        await self.update_message(interaction)

    @discord.ui.button(label="初期化", style=discord.ButtonStyle.danger, row=2)
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog.reset_settings()
        self.update_buttons()
        await interaction.response.edit_message(content="設定が初期化されました。", view=self)
        
    @discord.ui.button(label="実行", style=discord.ButtonStyle.success, row=2)
    async def execute(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.random_hero(interaction)

    def toggle_setting(self, setting, button):
        if setting in self.cog.selected_roles or setting in self.cog.selected_types:
            if setting in self.cog.selected_roles:
                if len(self.cog.selected_roles) > 1:
                    self.cog.selected_roles.remove(setting)
                else:
                    return
            if setting in self.cog.selected_types:
                if len(self.cog.selected_types) > 1:
                    self.cog.selected_types.remove(setting)
                else:
                    return
        else:
            if setting in {"アタッカー", "スプリンター", "ガンナー", "タンク"}:
                self.cog.selected_roles.add(setting)
            else:
                self.cog.selected_types.add(setting)
        self.update_buttons()

    async def update_message(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self)

    def update_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                emoji_id = child.emoji.id if isinstance(child.emoji, discord.PartialEmoji) else None
                if emoji_id == 1249625709517733941:  # :at:
                    if "アタッカー" in self.cog.selected_roles:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary
                elif emoji_id == 1249625777235034195:  # :sp:
                    if "スプリンター" in self.cog.selected_roles:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary
                elif emoji_id == 1249625749854490686:  # :gn:
                    if "ガンナー" in self.cog.selected_roles:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary
                elif emoji_id == 1249625807836414002:  # :tn:
                    if "タンク" in self.cog.selected_roles:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary
                elif child.label == "オリジナル":
                    if "オリジナル" in self.cog.selected_types:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary
                elif child.label == "コラボ":
                    if "コラボ" in self.cog.selected_types:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}!')

@bot.event
async def setup_hook():
    await bot.add_cog(HeroRoulette(bot))

# ボットトークンを入力してください
load_dotenv()
TOKEN = os.getenv('kani_TOKEN')

bot.run(TOKEN)
