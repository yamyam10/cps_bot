import discord, os, random, asyncio, datetime, pytz, openai, aiohttp, gspread, pytesseract, json, firebase_admin, re
from discord.ext import commands, tasks
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from discord import ui
from firebase_admin import credentials, firestore

load_dotenv()

#TOKEN = os.getenv('kani_TOKEN')  # 🦀bot
TOKEN = os.getenv('cps_TOKEN')  # カスタム大会bot

SPREADSHEET_ID = os.getenv('spreadsheet_id')
SHEET_NAME = os.getenv('sheet_name')
CHANNEL_ID = int(os.getenv('channel_id_spreadsheet'))
FIREBASE_CREDENTIALS_JSON = os.getenv('firebase')

openai.api_key = os.getenv('openai')
model_engine = "gpt-3.5-turbo"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

private_key = os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n")
creds_data = {
    "type": "service_account",
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": private_key,
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('GOOGLE_CLIENT_EMAIL')}"
}

firebase_private_key = os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n")
firebase_data = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": firebase_private_key,
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40discordbot-cps.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)
gspread_client = gspread.authorize(creds)
last_row = 0

@bot.event
async def on_ready():
    print(f'ログインしました {bot.user}')

    target_channel_id = int(os.getenv('channel_id'))
    target_channel = bot.get_channel(target_channel_id)

    if target_channel:
        japan_timezone = pytz.timezone('Asia/Tokyo')
        now = datetime.datetime.now(japan_timezone)
        login_message = f"{now.strftime('%Y年%m月%d日')}{now.strftime('%H:%M:%S')} ログインしました"
        await target_channel.send(login_message)
    else:
        print("指定されたチャンネルが見つかりません。")

    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}個のコマンドを同期しました。")
    except Exception as e:
        print(e)

    check_for_updates.start()

@tasks.loop(seconds=30)
async def check_for_updates():
    global last_row

    try:
        # シートのデータを取得
        sheet = gspread_client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        data = sheet.get_all_values()

        # 新しい行が追加されているかを確認
        if len(data) > last_row:
            new_row = data[-1]  # 最後の行を取得
            last_row = len(data)

            # 埋め込みメッセージの作成
            embed = discord.Embed(
                title="匿名意見箱に新しいデータが追加されました！",
                color=discord.Colour.purple()
            )
            embed.add_field(name="新しい意見", value=str(new_row), inline=False)

            # 特定のチャンネルに通知を送信
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
            else:
                print("チャンネルが見つかりませんでした")

    except Exception as e:
        print(f"シートの更新チェック中にエラーが発生しました: {e}")

@bot.tree.command(name="help", description="コマンドの詳細表示")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="コマンド一覧", color=discord.Colour.purple())
    embed.add_field(name="", value="`/help：`コマンド詳細を表示。", inline=False)
    embed.add_field(name="", value="`/おみくじ：`運勢を占ってくれるよ。", inline=False)
    embed.add_field(name="", value="`/チーム分け @mention：`ランダムでチーム分け", inline=False)
    embed.add_field(name="", value="`/vcチーム分け ボイスチャンネル：`vcメンバーをランダムでチーム分け", inline=False)
    embed.add_field(name="", value="`/ヒーロー：`ランダムでヒーローを表示", inline=False)
    embed.add_field(name="", value="`/ヒーロー設定：`ロールなどを選んでランダムにヒーローを表示", inline=False)
    embed.add_field(name="", value="`/ステージ：`ランダムでステージを表示", inline=False)
    embed.add_field(name="", value="`/ロール削除：`ロール削除", inline=False)
    embed.add_field(name="", value="`/ダイス：`ダイスを振ってくれるよ。", inline=False)
    await interaction.response.send_message(embed=embed)

OMIKUJI_RESULTS = [
    ("大吉", 0.05),
    ("吉", 0.25),
    ("中吉", 0.55),
    ("小吉", 0.70),
    ("末吉", 0.95),
    ("大凶", 1.00)
]

@bot.tree.command(name="おみくじ", description="運勢を占ってくれるよ。")
async def おみくじ(interaction: discord.Interaction):
    result = random.random()
    for title, cumulative_probability in OMIKUJI_RESULTS:
        if result <= cumulative_probability:
            embed = discord.Embed(title=f'{interaction.user.mention} さんの運勢は「{title}」です！', color=discord.Colour.purple())
            await interaction.response.send_message(embed=embed)
            return
    # 範囲外の場合はエラーメッセージを送信する（累積確率が正しければ発生しないはず）
    embed = discord.Embed(title="ERROR", description="運勢の取得中にエラーが発生しました。", color=discord.Colour.purple())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="チーム分け", description="チーム分けをしてくれるよ。")
async def チーム分け(interaction: discord.Interaction, role: discord.Role):
    # ユーザーに応答を返す前に、処理が実行中であることを示す
    await interaction.response.defer()

    # 管理者ロールがない場合は無視
    if not discord.utils.get(interaction.user.roles, name="管理者"):
        await interaction.followup.send(embed=discord.Embed(title='このコマンドは管理者のみが実行できます。', color=discord.Colour.purple()))
        return

    # ロールに属するメンバーを取得してシャッフル
    members = role.members
    random.shuffle(members)

    # チーム分け
    teams = [members[i:i + 3] for i in range(0, len(members), 3)]

    # チームごとにメッセージとロールを作成・付与
    messages = []
    for i, team in enumerate(teams):
        team_name = chr(ord("A") + i)
        message = f"**チーム{team_name}**\n"
        message += "\n".join(f"- {member.mention}" for member in team)
        messages.append(message)

        role_name = f"チーム{team_name}"
        team_role = discord.utils.get(interaction.guild.roles, name=role_name) or await interaction.guild.create_role(name=role_name, mentionable=True)
        await asyncio.gather(*[member.add_roles(team_role) for member in team])

    # メッセージを一度に送信
    try:
        await interaction.followup.send("\n".join(messages))
        await asyncio.sleep(1)
    except discord.errors.NotFound:
        pass

@bot.tree.command(name="vcチーム分け", description="ボイスチャンネルにいるメンバーをチーム分けします。")
async def vcチーム分け(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await interaction.response.defer()

    if not discord.utils.get(interaction.user.roles, name="管理者"):
        await interaction.followup.send(embed=discord.Embed(title='このコマンドは管理者のみが実行できます。', color=discord.Colour.purple()))
        return

    members = [member for member in channel.members if not member.bot]

    if len(members) == 0:
        await interaction.followup.send("ボイスチャンネルにメンバーがいません。")
        return

    random.shuffle(members)

    teams = [members[i:i + 3] for i in range(0, len(members), 3)]

    messages = []
    for i, team in enumerate(teams):
        team_name = chr(ord("A") + i)
        message = f"**チーム{team_name}**\n"
        message += "\n".join(f"- {member.mention}" for member in team)
        messages.append(message)

        role_name = f"チーム{team_name}"
        team_role = discord.utils.get(interaction.guild.roles, name=role_name) or await interaction.guild.create_role(name=role_name, mentionable=True)
        await asyncio.gather(*[member.add_roles(team_role) for member in team])

    try:
        await interaction.followup.send("\n".join(messages))
        await asyncio.sleep(1)
    except discord.errors.NotFound:
        pass

@bot.tree.command(name="ステージ", description="ランダムでステージを表示")
async def ステージ(interaction: discord.Interaction):
    stage = random.randint(0, 18)  # 0~18
    if stage == 0:  # 0が出たとき
        stageimg = "stage1.jpg"
        file = discord.File(fp="stage/stage1.jpg", filename=stageimg, spoiler=False)
    elif stage == 1:
        stageimg = "stage2.jpg"
        file = discord.File(fp="stage/stage2.jpg", filename=stageimg, spoiler=False)
    elif stage == 2:
        stageimg = "stage3.jpg"
        file = discord.File(fp="stage/stage3.jpg", filename=stageimg, spoiler=False)
    elif stage == 3:
        stageimg = "stage4.jpg"
        file = discord.File(fp="stage/stage4.jpg", filename=stageimg, spoiler=False)
    elif stage == 4:
        stageimg = "stage5.jpg"
        file = discord.File(fp="stage/stage5.jpg", filename=stageimg, spoiler=False)
    elif stage == 5:
        stageimg = "stage6.jpg"
        file = discord.File(fp="stage/stage6.jpg", filename=stageimg, spoiler=False)
    elif stage == 6:
        stageimg = "stage7.jpg"
        file = discord.File(fp="stage/stage7.jpg", filename=stageimg, spoiler=False)
    elif stage == 7:
        stageimg = "stage8.jpg"
        file = discord.File(fp="stage/stage8.jpg", filename=stageimg, spoiler=False)
    elif stage == 8:
        stageimg = "stage9.jpg"
        file = discord.File(fp="stage/stage9.jpg", filename=stageimg, spoiler=False)
    elif stage == 9:
        stageimg = "stage10.jpg"
        file = discord.File(fp="stage/stage10.jpg", filename=stageimg, spoiler=False)
    elif stage == 10:
        stageimg = "stage11.jpg"
        file = discord.File(fp="stage/stage11.jpg", filename=stageimg, spoiler=False)
    elif stage == 11:
        stageimg = "stage12.jpg"
        file = discord.File(fp="stage/stage12.jpg", filename=stageimg, spoiler=False)
    elif stage == 12:
        stageimg = "stage13.jpg"
        file = discord.File(fp="stage/stage13.jpg", filename=stageimg, spoiler=False)
    elif stage == 13:
        stageimg = "stage14.jpg"
        file = discord.File(fp="stage/stage14.jpg", filename=stageimg, spoiler=False)
    elif stage == 14:
        stageimg = "stage15.jpg"
        file = discord.File(fp="stage/stage15.jpg", filename=stageimg, spoiler=False)
    elif stage == 15:
        stageimg = "stage16.jpg"
        file = discord.File(fp="stage/stage16.jpg", filename=stageimg, spoiler=False)
    elif stage == 16:
        stageimg = "stage17.jpg"
        file = discord.File(fp="stage/stage17.jpg", filename=stageimg, spoiler=False)
    elif stage == 17:
        stageimg = "stage18.jpg"
        file = discord.File(fp="stage/stage18.jpg", filename=stageimg, spoiler=False)
    elif stage == 18:
        stageimg = "stage19.jpg"
        file = discord.File(fp="stage/stage19.jpg", filename=stageimg, spoiler=False)
    else:  # それ以外なのでERRORが出た時に処理される
        print("sutageエラー")
    await interaction.response.send_message(file=file)

@bot.tree.command(name="ロール削除", description="全てのチームロールを一括で削除")
async def ロール削除(interaction: discord.Interaction):
    # 管理者ロールがない場合は無視
    if not discord.utils.get(interaction.user.roles, name="管理者"):
        embed = discord.Embed(title='このコマンドは管理者のみが実行できます。', color=discord.Colour.purple())
        await interaction.response.send_message(embed=embed)
        return

    guild = interaction.guild  # 直接interactionオブジェクトからguildを取得
    team_roles = ['チームA', 'チームB', 'チームC', 'チームD', 'チームE', 'チームF']

    for member in guild.members:
        for role in member.roles:
            if role.name in team_roles:
                await member.remove_roles(role)

    embed = discord.Embed(title='全てのチームロールを一括で削除しました。', color=discord.Colour.purple())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ダイス", description="ダイスを振ってくれるよ。")
async def ダイス(interaction: discord.Interaction):
    sides = 6  # デフォルトのサイコロの面数を設定
    result = random.randint(1, sides)
    await interaction.response.send_message(f'{sides}面のサイコロを振りました。結果は: {result}です。')

class DiceButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.dice_result = None

    @ui.button(label="サイコロを振る", style=discord.ButtonStyle.primary)
    async def roll_dice(self, interaction: discord.Interaction, button: ui.Button):
        dice = [random.randint(1, 6) for _ in range(3)]
        dice.sort()
        result_message, score = get_result(dice)
        
        self.dice_result = (dice, result_message, score)

        dice_file_name = f'dice_all/dice_{"".join(map(str, dice))}.jpg'

        # Embed作成
        embed = discord.Embed(
            title=f'{interaction.user.display_name} のサイコロの結果',
            description=f'{result_message}',
            color=discord.Color.purple()
        )

        # 画像を埋め込み
        embed.set_image(url=f'attachment://{os.path.basename(dice_file_name)}')

        # 画像ファイルを添付してメッセージ送信
        file = discord.File(dice_file_name, filename=os.path.basename(dice_file_name))
        await interaction.response.send_message(
            embed=embed,
            file=file
        )

def get_result(dice):
    if dice[0] == dice[1] == dice[2]:
        if dice[0] == 1:
            return ("ピンゾロ", 100)
        else:
            return ("アラシ", 50)
    elif dice == [1, 2, 3]:
        return ("ヒフミ", -10)
    elif dice == [4, 5, 6]:
        return ("シゴロ", 50)
    elif dice[0] == dice[1] or dice[1] == dice[2]:
        unique = set(dice)
        unique.remove(dice[1])
        remaining = unique.pop()
        return (f"{remaining}の目", remaining)
    else:
        return ("目なし", 0)

@bot.tree.command(name="チンチロ", description="チンチロができます")
async def チンチロ(interaction: discord.Interaction):
    view = DiceButton()
    await interaction.response.send_message("サイコロを振りたい場合はボタンを押してね！", view=view)

# 通貨
CURRENCY = "BM"

# Firebase Firestoreの初期化
cred = credentials.Certificate(firebase_data)
firebase_admin.initialize_app(cred)
db = firestore.client()
manual_dice_rolls = {}

# Firestoreからユーザーの所持金をロード
def load_balances():
    balances = {}
    debts = {}  # 借金データ

    docs = db.collection("balances").stream()
    for doc in docs:
        data = doc.to_dict()
        balances[doc.id] = data.get("balance", 0)
        debts[doc.id] = data.get("debt", 0)  # デフォルトで0（借金なし）

    return balances, debts  # 所持金と借金を両方返す

def save_balances(balances, debts):
    """Firestoreにユーザーの所持金データと借金データを保存"""
    for user_id, balance in balances.items():
        debt = debts.get(user_id, 0)  # デフォルトで0
        db.collection("balances").document(user_id).set({"balance": balance, "debt": debt})

balances, debts = load_balances()

def ensure_balance(user_id):
    """ユーザーの初期所持金を確保"""
    user_id = str(user_id)

    balances, debts = load_balances()

    if user_id not in balances:
        balances[user_id] = 50000  # 初期所持金
        debts[user_id] = 0  # 初期借金なし
        save_balances(balances, debts)  # Firestore に保存

# 出目の役と倍率を取得
def get_vs_result(dice):
    dice.sort()
    if dice[0] == dice[1] == dice[2]:
        if dice[0] == 1:
            return ("ピンゾロ", 5)
        else:
            return (f"アラシ", 3)
    elif dice == [4, 5, 6]:
        return ("シゴロ", 2)
    elif dice == [1, 2, 3]:
        return ("ヒフミ", -2)
    elif dice[0] == dice[1] or dice[1] == dice[2]:
        unique = set(dice)
        unique.remove(dice[1])
        remaining = unique.pop()
        return (f"{remaining}の目", 1)
    else:
        return ("目なし", -1)

# 出目の強さを決定
def get_strength(dice):
    dice.sort()
    if dice[0] == dice[1] == dice[2]:
        return 100 if dice[0] == 1 else 90
    elif dice == [4, 5, 6]:
        return 80
    elif dice == [1, 2, 3]:
        return -1
    elif dice[0] == dice[1] or dice[1] == dice[2]:
        unique = set(dice)
        unique.remove(dice[1])
        remaining = unique.pop()
        return 40 - (6 - remaining) * 5
    else:
        return 0

def kanji2num(text):
    """漢数字と数字が混ざった表記を数値に変換する"""
    kanji_dict = {
        "十": 10, "百": 100, "千": 1000,
        "万": 10000, "億": 100000000, "兆": 1000000000000
    }

    num = 0
    temp = 0  # 一時的な数値
    section_total = 0  # 「万」「億」「兆」単位で累積する
    last_unit = 1  # 最後の単位（「万」「億」など）

    # 漢数字と数字の混合を考慮して、すべての数字を統一
    text = re.sub(r"(\d+)", lambda m: str(int(m.group(1))), text)  # 全角数字を半角に変換
    text = text.replace("０", "0").replace("１", "1").replace("２", "2") \
               .replace("３", "3").replace("４", "4").replace("５", "5") \
               .replace("６", "6").replace("７", "7").replace("８", "8") \
               .replace("９", "9")

    for char in text:
        if char.isdigit():
            temp = temp * 10 + int(char)  # 連続する数字を数値化
        elif char in kanji_dict:
            unit = kanji_dict[char]
            if unit >= 10000:  # 万・億・兆の処理
                if temp == 0:
                    temp = 1  # 「万」などの前に数字がない場合は1万として扱う
                section_total += temp * last_unit  # 現在のセクションを合計
                num += section_total * unit  # 「万」「億」「兆」ごとに計算
                section_total = 0  # セクションリセット
                last_unit = unit
                temp = 0
            else:
                if temp == 0:
                    temp = 1  # 例えば「十万」の場合、十の前が空なので1として扱う
                section_total += temp * unit
                temp = 0
        else:
            return None  # 無効な文字が含まれていたら変換不可

    num += section_total + temp  # 最後に残った数値を加算
    return num

class Dice_vs_Button(ui.View):
    def __init__(self, user1, user2, bot):
        super().__init__(timeout=None)
        self.user1 = user1
        self.user2 = user2
        self.bot = bot
        self.dice_result = {}
        self.bet_amount = 0
        self.game_over = False
        self.roll_attempts = {user1.id: 0, user2.id: 0}

    async def roll_dice_bot(self, interaction):
        if not self.user2.bot:
            return

        max_attempts = 3  # 最大3回まで振れる
        attempts = 0

        while attempts < max_attempts:
            dice = [random.randint(1, 6) for _ in range(3)]
            result_message, multiplier = get_vs_result(dice)
            strength = get_strength(dice)

            self.dice_result[self.bot.user.id] = (dice, result_message, multiplier, strength)

            # 目なしなら振り直し
            if result_message == "目なし":
                attempts += 1
                if attempts < max_attempts:
                    continue  # もう一度振る
            break  # 目なしでない or 3回振り終えたら終了

        # **親の役が確定するまでBotの結果を表示しない**
        if self.user1.id not in self.dice_result:
            return

        if self.roll_attempts[self.user1.id] >= 3 or self.dice_result[self.user1.id][2] != -1:
            await self.show_bot_dice_result(interaction)

            if len(self.dice_result) == 2:
                await self.determine_winner(interaction)

    async def show_bot_dice_result(self, interaction):
        if not self.user2.bot:
            return

        dice, result_message, _, _ = self.dice_result[self.bot.user.id]

        dice_file_name = f'dice_all/dice_{"".join(map(str, dice))}.jpg'
        embed = discord.Embed(
            title=f'{self.bot.user.mention} (子) のサイコロの結果',
            description=f'{result_message}',
            color=discord.Color.purple()
        )
        embed.set_image(url=f'attachment://{os.path.basename(dice_file_name)}')
        file = discord.File(dice_file_name, filename=os.path.basename(dice_file_name))

        await interaction.followup.send(embed=embed, file=file)

    def disable_buttons(self):
        """ボタンを無効化し、対戦終了"""
        for child in self.children:
            child.disabled = True
        self.stop()

    @ui.button(label="かけ金を設定 (親)", style=discord.ButtonStyle.success)
    async def set_bet(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user1.id:
            await interaction.response.send_message("親ユーザーのみかけ金を設定できます。", ephemeral=True)
            return

        balances, debts = load_balances()
        if balances.get(str(self.user1.id), 0) <= 0:
            await interaction.response.send_message("所持金がないため、チンチロ対戦を開始できません。", ephemeral=True)
            return

        if self.bet_amount > 0:
            await interaction.response.send_message(f"すでに掛け金 {self.bet_amount} {CURRENCY} が設定されています。", ephemeral=True)
            return

        if hasattr(self, "betting_in_progress") and self.betting_in_progress:
            await interaction.response.send_message("現在、掛け金の入力中です。少しお待ちください。", ephemeral=True)
            return

        self.betting_in_progress = True

        await interaction.response.send_message("掛け金を入力してください！", ephemeral=True)

        def check(msg):
            return msg.author.id == self.user1.id and msg.channel == interaction.channel

        try:
            bet_msg = await bot.wait_for("message", check=check, timeout=30)  # 30秒以内の入力を要求
            bet_input = bet_msg.content.strip()

            # 漢数字かどうかを判定
            if re.search(r"[一二三四五六七八九十百千万億]", bet_input):
                bet_amount = kanji2num(bet_input)
            else:
                bet_amount = int(bet_input)

            # 変換に失敗した場合
            if bet_amount is None or bet_amount <= 0 or bet_amount > balances.get(str(self.user1.id), 0):
                await interaction.followup.send("無効な掛け金です。所持金の範囲内で正しい数字を入力してください。", ephemeral=True)
                self.betting_in_progress = False  # 入力失敗時にフラグをリセット
                return

            self.bet_amount = bet_amount
            await interaction.followup.send(f"掛け金を {self.bet_amount} {CURRENCY} に設定しました！")

        except ValueError:
            await interaction.followup.send("無効な金額です。数値または漢数字（例: `５万`）を入力してください。", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("掛け金の入力時間が切れました。もう一度ボタンを押してください。", ephemeral=True)

        self.betting_in_progress = False
        
    @ui.button(label="サイコロを振る (親)", style=discord.ButtonStyle.primary)
    async def roll_dice_user1(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user1.id:
            await interaction.response.send_message("このボタンは親のみが押せます。", ephemeral=True)
            return
        await self.roll_dice(interaction, self.user1.id, self.user1.mention, "親")

    @ui.button(label="サイコロを振る (子)", style=discord.ButtonStyle.secondary)
    async def roll_dice_user2(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user2.id:
            await interaction.response.send_message("このボタンは子のみが押せます。", ephemeral=True)
            return
        
        if self.user2.id == self.bot.user.id:
            await self.roll_dice_bot()
        else:
            await self.roll_dice(interaction, self.user2.id, self.user2.mention, "子")

    async def roll_dice(self, interaction, user_id, user_mention, role):
        if self.bet_amount == 0:
            await interaction.response.send_message("かけ金が設定されていません。親がかけ金を設定してください。", ephemeral=True)
            return
        
        if self.game_over:
            await interaction.response.send_message("対戦は終了しました。もう一度遊ぶには新しく開始してください。", ephemeral=True)
            return

        if user_id in self.dice_result:
            await interaction.response.send_message("既に確定したので振れません。", ephemeral=True)
            return

        # if user_id == self.user2.id:
        #     dice = [1, 2, 3]
        # else:
        #     dice = [1, 1, 1]

        if str(user_id) in manual_dice_rolls and self.roll_attempts[user_id] == 0:
            dice = manual_dice_rolls.pop(str(user_id))
        else:
            dice = [random.randint(1, 6) for _ in range(3)]

        # dice = [random.randint(1, 6) for _ in range(3)]
        result_message, multiplier = get_vs_result(dice)
        strength = get_strength(dice)
        self.roll_attempts[user_id] += 1
        
        dice_file_name = f'dice_all/dice_{"".join(map(str, dice))}.jpg'
        embed = discord.Embed(
            title=f'{user_mention} ({role}) のサイコロの結果',
            description=f'{result_message}',
            color=discord.Color.purple()
        )
        embed.set_image(url=f'attachment://{os.path.basename(dice_file_name)}')
        file = discord.File(dice_file_name, filename=os.path.basename(dice_file_name))

        await interaction.response.send_message(embed=embed, file=file)

        if multiplier == -1 and self.roll_attempts[user_id] < 3:
            return

        self.dice_result[user_id] = (dice, result_message, multiplier, strength)

        if len(self.dice_result) == 2 and not self.game_over:
            self.game_over = True
            await self.determine_winner(interaction)

    async def determine_winner(self, interaction):
        balances, debts = load_balances()
        user1_strength = self.dice_result[self.user1.id][3]
        user2_strength = self.dice_result[self.user2.id][3]

        if user1_strength == user2_strength:
            result_embed = discord.Embed(
                title="対戦結果",
                description=f"引き分け！\n"
                            f"{self.user1.mention} の所持金: {balances.get(str(self.user1.id), 0)}{CURRENCY}\n"
                            f"{self.user2.mention} の所持金: {balances.get(str(self.user2.id), 0)}{CURRENCY}",
                color=discord.Color.gold()
            )
            load_balances()
            await self.show_bot_dice_result(interaction)
            await interaction.followup.send(embed=result_embed)
            self.disable_buttons()
            self.game_over = True
            return

        winner = self.user1 if user1_strength > user2_strength else self.user2
        loser = self.user2 if winner == self.user1 else self.user1

        # 勝者・敗者の所持金を確保
        ensure_balance(winner.id)
        ensure_balance(loser.id)

        dice_result_winner = list(self.dice_result[winner.id])
        amount_won = self.bet_amount * abs(self.dice_result[winner.id][2])

        # 負けた側がヒフミ (1,2,3) だった場合、勝者の獲得額を2倍
        if self.dice_result[loser.id][0] == [1, 2, 3]:
            amount_won *= 2
            dice_result_winner[2] *= 2

        if winner.id != self.bot.user.id:
            balances[str(winner.id)] += amount_won
        if loser.id != self.bot.user.id:
            balances[str(loser.id)] -= amount_won

        if winner.id != self.bot.user.id or loser.id != self.bot.user.id:
            save_balances(balances, debts)

        result_embed = discord.Embed(
            title="対戦結果",
            description=f"{winner.mention} 勝利！\n"
                        f"掛け金 {self.bet_amount}{CURRENCY} の {dice_result_winner[2]} 倍で {amount_won}{CURRENCY} 獲得\n"
                        f"{self.user1.mention} の所持金: {balances.get(str(self.user1.id), 0)}{CURRENCY}\n"
                        f"{self.user2.mention} の所持金: {balances.get(str(self.user2.id), 0)}{CURRENCY}",
            color=discord.Color.gold()
        )
        load_balances()
        await self.show_bot_dice_result(interaction)
        await interaction.followup.send(embed=result_embed)

        self.disable_buttons()
        self.game_over = True

@bot.tree.command(name="チンチロ対戦", description="ユーザー同士またはBotとチンチロ対戦！")
async def チンチロ対戦(interaction: discord.Interaction, opponent: discord.Member):
    if interaction.user.id == opponent.id:
        await interaction.response.send_message("自分自身とは対戦できません！他のユーザーを指定してください。", ephemeral=True)
        return
    
    ensure_balance(interaction.user.id)
    balances, debts = load_balances()
    if opponent.id != bot.user.id:
        ensure_balance(opponent.id)

    if balances.get(str(interaction.user.id), 0) <= 0:
        await interaction.response.defer()  # 応答を遅延させる
        await interaction.followup.send("所持金がないため、チンチロ対戦を開始できません。", ephemeral=True)
        return

    if opponent.id != bot.user.id and balances.get(str(opponent.id), 0) <= 0:
        await interaction.response.defer()
        await interaction.followup.send(f"{opponent.mention} の所持金がないため、チンチロ対戦を開始できません。", ephemeral=True)
        return

    view = Dice_vs_Button(interaction.user, opponent, bot)
    
    await interaction.response.defer()  # ここで応答を遅延させる
    await interaction.followup.send(f"{interaction.user.mention} vs {opponent.mention}！", view=view)

    # Botが対戦相手の場合、自動でサイコロを振る
    if opponent.id == bot.user.id:
        await view.roll_dice_bot(interaction)

@bot.tree.command(name="所持金変更", description="所持金を変更します")
async def 所持金変更(interaction: discord.Interaction, user: discord.User, amount: int):
    balances, debts = load_balances()
    admin_id = "513153492165197835"
    if str(interaction.user.id) != admin_id:
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    user_id = str(user.id)
    balances[user_id] += amount
    save_balances(balances, debts)

    embed = discord.Embed(
        title="所持金変更",
        description=f"{user.mention} の所持金を {amount} {CURRENCY}に設定しました。",
        color=discord.Color.purple()
    )
    embed.add_field(name="現在の所持金", value=f"{balances[user_id]} {CURRENCY}", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="所持金ランキング", description="全ユーザーの所持金ランキングを表示")
async def 所持金ランキング(interaction: discord.Interaction):
    await interaction.response.defer()

    balances, debts = load_balances()

    if not balances:
        await interaction.followup.send("現在、所持金のデータがありません。", ephemeral=True)
        return

    user_id = str(interaction.user.id)

    total_assets = {
        uid: balances.get(uid, 0) - debts.get(uid, 0) for uid in balances
    }

    sorted_assets = sorted(total_assets.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="所持金ランキング",
        color=discord.Color.purple()
    )

    user_rank = None
    user_balance_text = None
    rank = 0

    displayed_count = 0

    for uid, net_worth in sorted_assets:
        if str(uid) == str(bot.user.id):
            continue

        try:
            user = await bot.fetch_user(int(uid))
            if user.bot:
                continue
            user_display = user.mention
        except discord.NotFound:
            user_display = f"`{uid}`"
        except discord.HTTPException:
            user_display = f"`{uid}`"

        balance = balances.get(uid, 0)
        debt_amount = debts.get(uid, 0)

        if debt_amount > 0:
            balance_text = f"{balance} {CURRENCY} (借金: {debt_amount} {CURRENCY})"
        else:
            balance_text = f"{balance} {CURRENCY}"

        rank += 1

        if displayed_count < 10:
            embed.add_field(name=f"{rank}位 {user_display}", value=f"総資産: {net_worth} {CURRENCY}\n{balance_text}", inline=False)
            displayed_count += 1
        
        if uid == user_id:
            user_rank = rank
            user_balance_text = f"総資産: {net_worth} {CURRENCY}\n{balance_text}"

    if user_rank and user_rank > 10:
        embed.add_field(name=f"\n--- あなたの順位 ---", value=f"#{user_rank} {interaction.user.mention}: {user_balance_text}", inline=False)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="所持金", description="自分の所持金を表示")
async def 所持金(interaction: discord.Interaction):
    balances, debts = load_balances()
    user_id = str(interaction.user.id)

    balance = balances.get(user_id, 0)
    debt_amount = debts.get(user_id, 0)

    if debt_amount > 0:
        balance_text = f"{balance} {CURRENCY} (借金: {debt_amount} {CURRENCY})"
    else:
        balance_text = f"{balance} {CURRENCY}"

    embed = discord.Embed(
        title=f"{interaction.user.mention}の所持金",
        description=f"{balance_text}",
        color=discord.Color.purple()
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="借金", description="最大5万ずつ借金可能")
async def 借金(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    admin_ids = ["513153492165197835", "698894367225544735"]

    if amount <= 0:
        await interaction.followup.send("借金額は正の数を入力してください。", ephemeral=True)
        return

    ensure_balance(user_id)

    max_allowed_loan = 50000
    if user_id not in admin_ids and amount > max_allowed_loan:
        await interaction.followup.send(f"1回の借金は最大 {max_allowed_loan} {CURRENCY} までです。", ephemeral=True)
        return

    balances, debts = load_balances()

    # 借金前の所持金がマイナスの場合
    if balances[user_id] < 0:
        required_amount = 50000 - balances[user_id]
        debts[user_id] += required_amount
        balances[user_id] = 50000
    else:
        # 通常の借金処理
        debts[user_id] += amount
        balances[user_id] += amount

    save_balances(balances, debts)

    embed = discord.Embed(
        title="借金完了",
        description=f"{interaction.user.mention} は **{amount} {CURRENCY}** 借りました。\n"
                    f"**現在の所持金:** {balances[user_id]} {CURRENCY}\n"
                    f"**現在の借金:** {debts[user_id]} {CURRENCY}",
        color=discord.Color.red()
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="借金返済", description="借金を返済できます")
async def 借金返済(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)  

    user_id = str(interaction.user.id)

    if amount <= 0:
        await interaction.followup.send("返済額は正の数を入力してください。", ephemeral=True)
        return

    # Firestore からデータ取得
    balances, debts = load_balances()

    current_debt = debts.get(user_id, 0)  # 借金額を取得
    if current_debt == 0:
        await interaction.followup.send("借金はありません！", ephemeral=True)
        return

    # 返済額が借金を超えないようにする
    repayment_amount = min(amount, current_debt, balances[user_id])

    if repayment_amount <= 0:
        await interaction.followup.send("所持金が足りないため、借金を返済できません。", ephemeral=True)
        return

    # 返済処理
    debts[user_id] -= repayment_amount
    balances[user_id] -= repayment_amount  # 所持金から減らす

    # Firestore に保存
    save_balances(balances, debts)

    embed = discord.Embed(
        title="借金返済",
        description=f"{interaction.user.mention} は {repayment_amount} {CURRENCY} 返済しました。\n現在の所持金: {balances[user_id]} {CURRENCY}\n残りの借金: {debts[user_id]} {CURRENCY}",
        color=discord.Color.green()
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.command()
async def test(ctx):
    embed = discord.Embed(title="正常に動作しています。", color=discord.Colour.purple())
    await ctx.send(embed=embed)

@bot.command(name="出目設定")
async def 出目設定(ctx, *, dice_input: str):
    admin_ids = ["513153492165197835", "1075092388835512330"]

    if str(ctx.author.id) not in admin_ids:
        await ctx.send("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    try:
        dice = [int(num) for num in dice_input.split(",")]
        if len(dice) != 3 or any(d < 1 or d > 6 for d in dice):
            raise ValueError

        manual_dice_rolls[str(ctx.author.id)] = dice
        print(f"出目設定: {ctx.author.id} -> {dice}")

        await ctx.send(f"出目を {dice} に設定しました！", ephemeral=True)

    except ValueError:
        await ctx.send("正しい形式で入力してください！ 例: `!出目設定 1,1,1`", ephemeral=True)

@bot.command(name="出目確認")
async def 出目確認(ctx):
    if not manual_dice_rolls:
        await ctx.send("現在設定されている出目はありません。", delete_after=5)
        return

    message = "**現在設定されている出目:**\n"
    for user_id, dice in manual_dice_rolls.items():
        message += f"<@{user_id}>: {dice}\n"

    await ctx.send(message, delete_after=5)

@bot.command(name="履歴削除", description="メッセージ履歴を全て削除します。")
async def 履歴削除(ctx):
    channel = ctx.channel
    messages = []
    async for message in channel.history(limit=None):
        messages.append(message)

    for chunk in [messages[i:i + 100] for i in range(0, len(messages), 100)]:
        await channel.delete_messages(chunk)

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
            {"id": 82, "name": "ターニャ・デグレチャフ", "color": 0x47574f, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1248333510805028915/37139A0F-1D30-4EF4-9A02-C42240080BBF.jpg"},
            {"id": 83, "name": "鬼ヶ式 うら", "color": 0xb7a79e, "type": "オリジナル", "role": "タンク", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1289240020607045653/2EC4D3C2-CB84-44D6-AE0C-8B2C8D0924C7.jpg"},
            {"id": 84, "name": "コラプス", "color": 0x8a57fb, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1289240154309136445/F7F9E844-4FCB-4E4C-8579-487DD43A6B28.jpg"},
            {"id": 85, "name": "ボンドルド", "color": 0x61388a, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1332202734002241556/E0A3FC6E-42A5-49F4-A846-7EF87C20492C.jpg"},
            {"id": 86, "name": "みりぽゆ", "color": 0xff68c8, "type": "オリジナル", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1332202734228602981/65E81500-A051-4523-8E40-5E83B7097946.jpg"},
            {"id": 87, "name": "ゴン=フリークス", "color": 0x49c334, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1332202734463746241/2E660FE9-0E9B-450B-B5AA-A345364BD67E.jpg"},
            {"id": 88, "name": "キルア=ゾルディック", "color": 0xac85bc, "type": "コラボ", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1332202734719336499/E669E432-110C-49B6-A7AF-27EBBA049949.jpg"},
            {"id": 89, "name": "チーちゃん", "color": 0xd8ef3c, "type": "オリジナル", "role": "スプリンター", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1344942868510543894/7BEC30AF-6F7E-4ABB-AA35-4CA532E3E283.jpg"}

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

    @app_commands.command(name="ヒーロー設定", description="ロールなどを選んでランダムにヒーローを表示")
    async def setup_roulette(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=RouletteSettingsView(self), ephemeral=True)

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

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji=":at:1249776411237941359")
    async def attacker(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle_setting("アタッカー", button)
        await self.update_message(interaction)

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji=":sp:1249776620039045280")
    async def sprinter(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle_setting("スプリンター", button)
        await self.update_message(interaction)

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji=":gn:1249776475532562483")
    async def gunner(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle_setting("ガンナー", button)
        await self.update_message(interaction)

    @discord.ui.button(label="", style=discord.ButtonStyle.primary, emoji=":tn:1249776553009615030")
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
        await interaction.response.edit_message(view=self)
        
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
                if emoji_id == 1249776411237941359:  # :at:
                    if "アタッカー" in self.cog.selected_roles:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary
                elif emoji_id == 1249776620039045280:  # :sp:
                    if "スプリンター" in self.cog.selected_roles:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary
                elif emoji_id == 1249776475532562483:  # :gn:
                    if "ガンナー" in self.cog.selected_roles:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary
                elif emoji_id == 1249776553009615030:  # :tn:
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

@bot.event
async def setup_hook():
    await bot.add_cog(HeroRoulette(bot))

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    log_channel_id = int(os.getenv('channel_id_message'))
    log_channel = bot.get_channel(log_channel_id)

    if log_channel:
        if not message.content and message.attachments:
            embed = discord.Embed(title="メッセージ削除", description="添付ファイル付き", color=discord.Color.red())
        else:
            embed = discord.Embed(title="メッセージ削除", description=f"削除されたメッセージ: {message.content or '（メッセージなし）'}", color=discord.Color.red())

        embed.add_field(name="ユーザー", value=f"{message.author.mention}（{message.author}）", inline=True)
        embed.add_field(name="チャンネル", value=message.channel.mention, inline=True)
        embed.set_footer(text=f"メッセージID: {message.id}")

        await log_channel.send(embed=embed)

        if message.attachments:
            temp_folder = "temp_files"
            os.makedirs(temp_folder, exist_ok=True)

            for attachment in message.attachments:
                file_path = os.path.join(temp_folder, attachment.filename)
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            with open(file_path, 'wb') as f:
                                f.write(await resp.read())
                            await log_channel.send(f"削除されたファイル: {attachment.filename}", file=discord.File(file_path))
                            await asyncio.sleep(60)
                            os.remove(file_path)

# @bot.event
# async def on_message(message):
#     global model_engine
#     if message.author.bot:
#         return
#     if message.author == bot.user:
#         return

#     # メンションに反応
#     if bot.user in message.mentions:
#         try:
#             # プロンプトをそのまま使用
#             prompt = message.content.strip()
#             if not prompt:
#                 await message.channel.send("質問内容がありません")
#                 return
            
#             # OpenAIのChat APIを使用して応答を生成
#             completion = openai.ChatCompletion.create(
#                 model=model_engine,
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "送られてきた文章に対して優しく返信してください。"
#                     },
#                     {
#                         "role": "user",
#                         "content": prompt
#                     }
#                 ],
#             )

#             response = completion.choices[0].message['content']
#             await message.channel.send(response)
#         except openai.error.RateLimitError:
#             await message.channel.send("現在のAPI使用量制限を超えています。プランのアップグレードや使用量の確認を行ってください。")
#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             await message.channel.send("エラーが発生しました。")

bot.run(TOKEN)