import discord, os, random, asyncio, datetime, pytz, openai, aiohttp, gspread, pytesseract, json, firebase_admin, cv2
from discord.ext import commands, tasks
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from discord import ui
from firebase_admin import credentials, firestore
import numpy as np

load_dotenv()

TOKEN = os.getenv('kani_TOKEN')  # 🦀bot
#TOKEN = os.getenv('cps_TOKEN')  # カスタム大会bot
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
gspread_client = gspread.authorize(creds)  # gspread用のクライアント

SPREADSHEET_ID = os.getenv('spreadsheet_id')
SHEET_NAME = os.getenv('sheet_name')
CHANNEL_ID = int(os.getenv('channel_id_kani'))
FIREBASE_CREDENTIALS_JSON = os.getenv('firebase')

last_row = 0

@bot.event
async def on_ready():
    print(f'ログインしました {bot.user}')

    # メッセージを送信するチャンネルを取得
    target_channel_id = int(os.getenv('channel_id_kani'))
    target_channel = bot.get_channel(target_channel_id)

    # メッセージを送信
    if target_channel:
        japan_timezone = pytz.timezone('Asia/Tokyo')
        now = datetime.datetime.now(japan_timezone)
        login_message = f"{now.strftime('%Y年%m月%d日')}{now.strftime('%H:%M:%S')} ログインしました"
        await target_channel.send(login_message)
    else:
        print("指定されたチャンネルが見つかりません。")

    # スラッシュコマンド同期
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}個のコマンドを同期しました。")
    except Exception as e:
        print(e)

    # シート監視タスクをバックグラウンドで開始
    check_for_updates.start()

@tasks.loop(seconds=30)  # 30秒ごとに実行
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
            embed.add_field(name="", value=str(new_row), inline=False)

            # 特定のチャンネルに通知を送信
            channel = bot.get_channel(CHANNEL_ID)
            await channel.send(embed=embed)

    except Exception as e:
        print(f"シートの更新チェック中にエラーが発生しました: {e}")

@bot.tree.command(name="help", description="コマンドの詳細表示")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="コマンド一覧", color=discord.Colour.purple())
    embed.add_field(name="", value="`/help：`コマンド詳細を表示。", inline=False)
    embed.add_field(name="", value="`/おみくじ：`運勢を占ってくれるよ。", inline=False)
    embed.add_field(name="", value="`/チーム分け @mention：`ランダムでチーム分け", inline=False)
    embed.add_field(name="", value="`/ヒーロー：`ランダムでヒーローを表示", inline=False)
    embed.add_field(name="", value="`/ヒーロー設定：`ロールなどを選んでランダムにヒーローを表示", inline=False)
    embed.add_field(name="", value="`/ステージ：`ランダムでステージを表示", inline=False)
    embed.add_field(name="", value="`/ロール削除：`ロール削除", inline=False)
    embed.add_field(name="", value="`/ダイス：`ダイスを振ってくれるよ。", inline=False)
    await interaction.response.send_message(embed=embed)

# おみくじの結果と累積確率を定義
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

@bot.tree.command(name="チーム分け", description="ボイスチャンネルにいるメンバーをチーム分けします。")
async def チーム分け(interaction: discord.Interaction, channel: discord.VoiceChannel):
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

# ユーザーの所持金データファイル
BALANCE_FILE = "balances.json"

# データを読み込む関数
def load_balances():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            return json.load(f)
    return {}

# データを保存する関数
def save_balances(balances):
    with open(BALANCE_FILE, "w") as f:
        json.dump(balances, f, indent=4)

balances = load_balances()

class DiceButton(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)
        self.dice_result = None

    @ui.button(label="サイコロを振る", style=discord.ButtonStyle.primary)
    async def roll_dice(self, interaction: discord.Interaction, button: ui.Button):
        if self.user_id not in balances:
            balances[self.user_id] = 50000

        # かけ金を確認
        await interaction.response.send_message("かけ金を入力してください！", ephemeral=True)
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel
        
        bet_msg = await bot.wait_for("message", check=check)
        try:
            bet_amount = int(bet_msg.content)
        except ValueError:
            await interaction.followup.send("無効な金額です。数値を入力してください。", ephemeral=True)
            return

        if bet_amount <= 0 or bet_amount > balances[self.user_id]:
            await interaction.followup.send("無効なかけ金です。所持金の範囲内で入力してください。", ephemeral=True)
            return
        
        dice = [random.randint(1, 6) for _ in range(3)]
        dice.sort()
        result_message, score = get_result(dice)
        
        self.dice_result = (dice, result_message, score)

        # 勝敗判定と所持金の更新
        if score > 0:
            balances[self.user_id] += bet_amount * (score / 10)
        else:
            balances[self.user_id] -= bet_amount
        save_balances(balances)
        
        dice_file_name = f'dice_all/dice_{"".join(map(str, dice))}.jpg'
        
        embed = discord.Embed(
            title=f'{interaction.user.display_name} のサイコロの結果',
            description=f'{result_message}\n現在の所持金: {balances[self.user_id]}{CURRENCY}',
            color=discord.Color.purple()
        )
        embed.set_image(url=f'attachment://{os.path.basename(dice_file_name)}')
        
        file = discord.File(dice_file_name, filename=os.path.basename(dice_file_name))
        await interaction.followup.send(embed=embed, file=file)

def get_result(dice):
    dice.sort()
    if dice[0] == dice[1] == dice[2]:
        if dice[0] == 1:
            return ("ピンゾロ (5倍)！", 100)
        else:
            return (f"アラシ ({dice[0]}のぞろ目, 3倍)！", 90)
    elif dice == [4, 5, 6]:
        return ("シゴロ (2倍)！", 80)
    elif dice == [1, 2, 3]:
        return ("ヒフミ (-2倍)！", -10)
    elif dice[0] == dice[1] or dice[1] == dice[2]:
        unique = set(dice)
        unique.remove(dice[1])
        remaining = unique.pop()
        return (f"{remaining}の目 (1倍)", 40 - (6 - remaining) * 5)
    else:
        return ("目なし", 0)

@bot.tree.command(name="チンチロ", description="チンチロで遊べます！")
async def チンチロ(interaction: discord.Interaction):
    view = DiceButton(interaction.user.id)
    await interaction.response.send_message("サイコロを振りたい場合はボタンを押してね！", view=view)

# 通貨
CURRENCY = "BM"

# Firebase Firestoreの初期化
cred = credentials.Certificate(firebase_data)
firebase_admin.initialize_app(cred)
db = firestore.client()

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
            bet_amount = int(bet_msg.content)

            if bet_amount <= 0 or bet_amount > balances.get(str(self.user1.id), 0):
                await interaction.followup.send("無効な掛け金です。所持金の範囲内で入力してください。", ephemeral=True)
                self.betting_in_progress = False  # 入力失敗時にフラグをリセット
                return

            self.bet_amount = bet_amount
            await interaction.followup.send(f"掛け金を {self.bet_amount} {CURRENCY} に設定しました！")

        except ValueError:
            await interaction.followup.send("無効な金額です。数値を入力してください。", ephemeral=True)
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

        dice = [random.randint(1, 6) for _ in range(3)]
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

    if amount <= 0:
        await interaction.followup.send("借金額は正の数を入力してください。", ephemeral=True)
        return

    ensure_balance(user_id)  # ユーザーの初期データ確保

    max_allowed_loan = 50000  # 1回の最大借金額
    if amount > max_allowed_loan:
        await interaction.followup.send(f"1回の借金は最大 {max_allowed_loan} {CURRENCY} までです。", ephemeral=True)
        return

    # Firestore からデータ取得
    balances, debts = load_balances()

    # 借金を増やし、所持金を追加
    debts[user_id] = debts.get(user_id, 0) + amount
    balances[user_id] += amount  # 借金した分、所持金を増やす

    # Firestore に保存
    save_balances(balances, debts)

    embed = discord.Embed(
        title="借金完了",
        description=f"{interaction.user.mention} は {amount} {CURRENCY} 借りました。\n現在の所持金: {balances[user_id]} {CURRENCY}\n現在の借金: {debts[user_id]} {CURRENCY}",
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

@bot.tree.command(name="プレイヤーデータ登録", description="自分の戦績データを登録します")
@app_commands.describe(
    total_matches="総試合数",
    wins="勝利数",
    current_rank="現在のランク（例: S9 ~ S1, Aなど）",
    season_history="過去のシーズン履歴（例: S4, S5）"
)
async def プレイヤーデータ登録(
    interaction: discord.Interaction,
    total_matches: int,
    wins: int,
    current_rank: str,
    season_history: str
):
    user_id = str(interaction.user.id)
    player_ref = db.collection("player_stats").document(user_id)
    player_ref.set({
        "total_matches": total_matches,
        "wins": wins,
        "current_rank": current_rank.upper(),
        "season_history": season_history,
        "name": interaction.user.name
    })

    win_rate = round((wins / total_matches) * 100, 1) if total_matches > 0 else 0
    embed = discord.Embed(title="戦績登録完了", color=discord.Color.green())
    embed.add_field(name="総試合数", value=str(total_matches), inline=True)
    embed.add_field(name="勝利数", value=str(wins), inline=True)
    embed.add_field(name="勝率", value=f"{win_rate}%", inline=True)
    embed.add_field(name="現在のランク", value=current_rank.upper(), inline=False)
    embed.add_field(name="過去のシーズン履歴", value=season_history, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="公平チーム分け", description="実力を考慮して公平にチームを分けます。")
async def 公平チーム分け(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.defer()

    if not discord.utils.get(interaction.user.roles, name="管理者"):
        await interaction.followup.send(embed=discord.Embed(title='このコマンドは管理者のみが実行できます。', color=discord.Colour.purple()))
        return

    members = role.members
    if len(members) < 3:
        await interaction.followup.send("メンバー数が足りません。最低3人必要です。", ephemeral=True)
        return

    # 余りが出た場合は削除
    remainder = len(members) % 3
    if remainder != 0:
        members = members[:-remainder]

    rank_score_map = {
        "S9": 6500, "S8": 6000, "S7": 5500, "S6": 5000, "S5": 4500,
        "S4": 4000, "S3": 3500, "S2": 3000, "S1": 2500,
        "A": 2000, "B": 1500, "C": 1000, "D": 600, "E": 300, "F": 100
    }

    import firebase_admin
    from firebase_admin import credentials, firestore

    db = firestore.client()

    player_stats = {}
    for member in members:
        doc = db.collection("player_stats").document(str(member.id)).get()
        if doc.exists:
            data = doc.to_dict()
            rank = rank_score_map.get(data.get("現在のランク", "C"), 1000)
            season_history = [
                rank_score_map.get(rank_str.strip().upper(), 1000)
                for rank_str in data.get("過去のシーズン履歴", [])
            ]
            if len(season_history) == 0:
                season_history = [rank] * 3

            player_stats[str(member.id)] = {
                "matches": data.get("総試合数", 0),
                "wins": data.get("勝利数", 0),
                "rank": rank,
                "season_history": season_history
            }
        else:
            player_stats[str(member.id)] = {
                "matches": 0,
                "wins": 0,
                "rank": 1000,
                "season_history": [1000, 1000, 1000]
            }

    def calculate_score(data):
        win_rate = data["wins"] / data["matches"] if data["matches"] > 0 else 0
        season_avg = sum(data["season_history"]) / len(data["season_history"])
        return data["rank"] * 0.5 + win_rate * 1000 * 0.3 + season_avg * 0.2

    scored_members = [
        (member, calculate_score(player_stats[str(member.id)]))
        for member in members
    ]
    scored_members.sort(key=lambda x: x[1], reverse=True)

    teams = [[] for _ in range(len(members) // 3)]

    direction = 1
    team_index = 0
    for member, _ in scored_members:
        teams[team_index].append(member)
        team_index += direction
        if team_index >= len(teams) or team_index < 0:
            direction *= -1
            team_index += direction

    messages = []
    for i, team in enumerate(teams):
        team_name = chr(ord("A") + i)
        message = f"**チーム{team_name}**\n"
        message += "\n".join(f"- {member.mention}" for member in team)
        messages.append(message)

        role_name = f"チーム{team_name}"
        team_role = discord.utils.get(interaction.guild.roles, name=role_name) or await interaction.guild.create_role(name=role_name, mentionable=True)
        await asyncio.gather(*[member.add_roles(team_role) for member in team])

    await interaction.followup.send("\n\n".join(messages))

# 🔥 画像を保存するディレクトリ
IMAGE_SAVE_PATH = "./images"

# 🔥 HSV の範囲を手動で設定できるように定義（より厳密な黄色の検出）
HSV_RANGES = {
    "orange": {
        "lower": np.array([10, 150, 150]),
        "upper": np.array([30, 255, 255])
    },
    "yellow": {
        "lower": np.array([20, 100, 100]),
        "upper": np.array([40, 255, 255])
    }
}

# 🔥 画像を処理して超過エリアを判定する関数
def process_image(image_path, save_path="processed.png"):
    image = cv2.imread(image_path)
    image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 黄色のエリアを抽出
    mask_yellow = cv2.inRange(image_hsv, HSV_RANGES["yellow"]["lower"], HSV_RANGES["yellow"]["upper"])

    # オレンジ色のエリアを抽出
    mask_orange = cv2.inRange(image_hsv, HSV_RANGES["orange"]["lower"], HSV_RANGES["orange"]["upper"])

    # 黄色とオレンジの輪郭を取得
    contours_yellow, _ = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_orange, _ = cv2.findContours(mask_orange, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 🔥 黄色のエリアのマスク（青色で描画）
    yellow_area = np.zeros_like(mask_yellow)
    cv2.drawContours(yellow_area, contours_yellow, -1, (255), thickness=cv2.FILLED)

    # 🔥 黄色のエリアを青色で描画
    cv2.drawContours(image, contours_yellow, -1, (255, 0, 0), 2)

    # 🔥 画像の中心座標を取得
    height, width = mask_yellow.shape
    center_x, center_y = width // 2, height // 2

    # 🔥 十字の方向（上・下・左・右）でオレンジエリアが黄色を超えているか判定
    exceed_count = 0
    directions = {
        "上": (center_x, center_y - height // 4),
        "下": (center_x, center_y + height // 4),
        "左": (center_x - width // 4, center_y),
        "右": (center_x + width // 4, center_y),
    }

    for direction, (dx, dy) in directions.items():
        if 0 <= dx < width and 0 <= dy < height:
            if mask_orange[dy, dx] > 0 and mask_yellow[dy, dx] == 0:
                exceed_count += 1
                # 🔥 超過エリアを赤色でマーク
                cv2.circle(image, (dx, dy), 10, (0, 0, 255), -1)

    # 🔥 可視化画像を保存
    cv2.imwrite(save_path, image)

    return exceed_count, save_path  # 超過エリア数と保存した画像のパスを返す

# 🔥 画像送信ボタンのクラス
class MoneyRequest(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    @discord.ui.button(label="画像を送る", style=discord.ButtonStyle.primary)
    async def send_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("このリクエストはあなたのものではありません！", ephemeral=True)
            return

        await interaction.response.send_message("画像を送信してください！", ephemeral=True)

        def check(msg):
            return msg.author.id == self.user.id and msg.attachments

        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            attachment = msg.attachments[0]

            if not attachment.filename.lower().endswith(("png", "jpg", "jpeg")):
                await msg.channel.send("画像ファイルのみ受け付けています。")
                return

            # 🔥 画像を保存するディレクトリを作成（存在しない場合）
            os.makedirs(IMAGE_SAVE_PATH, exist_ok=True)

            # 🔥 画像の保存パス
            image_path = os.path.join(IMAGE_SAVE_PATH, attachment.filename)
            await attachment.save(image_path)

            # 🔥 画像解析（可視化画像も作成）
            exceed_count, processed_image_path = process_image(image_path)
            reward = min(exceed_count, 4) * 1000  # 最大4000BM

            # 🔥 Firestoreの balances に金額を反映
            balances, debts = load_balances()
            user_id = str(msg.author.id)

            balances.setdefault(user_id, 0)
            balances[user_id] += reward
            save_balances(balances, debts)

            # 🔥 可視化した画像を送信
            with open(processed_image_path, "rb") as f:
                file = discord.File(f, filename="processed.png")
                await msg.channel.send(
                    content=f"画像を確認しました！\n{exceed_count} か所の超過エリアがあり、{reward} BM を支払いました！💰",
                    file=file
                )

        except TimeoutError:
            await interaction.followup.send("時間切れです。もう一度コマンドを実行してください。", ephemeral=True)

@bot.tree.command(name="おかねほちぃねん", description="画像を送るとお金がもらえます")
async def おかねほちぃねん(interaction: discord.Interaction):
    view = MoneyRequest(interaction.user)
    await interaction.response.send_message("画像を送るにはボタンをクリックしてください！", view=view, ephemeral=True)


from collections import defaultdict, deque

# サーバーごとの再生キュー（deque = 高速なキュー）
music_queues = defaultdict(deque)

@bot.tree.command(name="songs", description="再生できる曲の一覧を表示します。")
async def songs(interaction: discord.Interaction):
    music_dir = "./music"
    files = sorted([f[:-4] for f in os.listdir(music_dir) if f.endswith(".mp3")])
    if not files:
        await interaction.response.send_message("再生可能な曲が見つかりません。")
        return
    msg = "🎶 **再生できる曲一覧**\n" + "\n".join(f"{i+1}. `{f}`" for i, f in enumerate(files))
    await interaction.response.send_message(msg)

@bot.tree.command(name="play", description="番号で曲をキューに追加して再生します。")
@app_commands.describe(index="再生したい曲の番号（/songsで確認）")
async def play(interaction: discord.Interaction, index: int):
    guild_id = interaction.guild.id
    music_dir = "./music"
    files = sorted([f for f in os.listdir(music_dir) if f.endswith(".mp3")])

    if index < 1 or index > len(files):
        await interaction.response.send_message("❌ 無効な番号です。`/songs` で確認してください。", ephemeral=True)
        return

    filename = files[index - 1]
    filepath = os.path.join(music_dir, filename)

    # キューに追加
    music_queues[guild_id].append(filepath)
    await interaction.response.send_message(f"🎶 `{filename[:-4]}` をキューに追加しました。")

    # 再生中でなければ開始
    vc = interaction.guild.voice_client
    if vc is None or not vc.is_connected():
        if interaction.user.voice is None or interaction.user.voice.channel is None:
            await interaction.followup.send("❗️先にボイスチャンネルに参加してください。", ephemeral=True)
            return
        vc = await interaction.user.voice.channel.connect()

    if not vc.is_playing():
        play_next(interaction.guild, vc)

def play_next(guild, vc):
    queue = music_queues[guild.id]
    if not queue:
        coro = vc.disconnect()
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        fut.add_done_callback(lambda _: print(f"{guild.name} から切断しました"))
        return

    filepath = queue.popleft()
    vc.play(discord.FFmpegPCMAudio(filepath), after=lambda e: play_next(guild, vc))

def disconnect_if_empty(guild, vc):
    coro = vc.disconnect()
    fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
    fut.add_done_callback(lambda _: print(f"{guild.name}（1曲ランダム）から切断しました"))

@bot.tree.command(name="queue", description="現在の再生キューを表示します。")
async def queue(interaction: discord.Interaction):
    queue = music_queues[interaction.guild.id]
    if not queue:
        await interaction.response.send_message("🎵 キューは空です。")
        return
    msg = "**現在の再生キュー：**\n" + "\n".join(f"{i+1}. `{os.path.basename(path)[:-4]}`" for i, path in enumerate(queue))
    await interaction.response.send_message(msg)

@bot.tree.command(name="playall", description="全曲をキューに追加して再生します。")
async def playall(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    music_dir = "./music"
    files = sorted([f for f in os.listdir(music_dir) if f.endswith(".mp3")])
    if not files:
        await interaction.response.send_message("❌ 曲が見つかりません。")
        return

    for f in files:
        music_queues[guild_id].append(os.path.join(music_dir, f))

    await interaction.response.send_message("📜 全曲をキューに追加しました。")

    vc = interaction.guild.voice_client
    if vc is None or not vc.is_connected():
        if interaction.user.voice and interaction.user.voice.channel:
            vc = await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("❗️ボイスチャンネルに参加してください。", ephemeral=True)
            return

    if not vc.is_playing():
        play_next(interaction.guild, vc)

@bot.tree.command(name="playrandom", description="ランダムな1曲を再生します。")
async def playrandom(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    music_dir = "./music"
    files = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
    if not files:
        await interaction.response.send_message("❌ 曲が見つかりません。")
        return

    choice = random.choice(files)
    filepath = os.path.join(music_dir, choice)

    vc = interaction.guild.voice_client
    if vc is None or not vc.is_connected():
        if interaction.user.voice and interaction.user.voice.channel:
            vc = await interaction.user.voice.channel.connect()
        else:
            await interaction.response.send_message("❗️ボイスチャンネルに参加してください。", ephemeral=True)
            return

    if vc.is_playing():
        vc.stop()

    vc.play(discord.FFmpegPCMAudio(filepath), after=lambda e: disconnect_if_empty(interaction.guild, vc))
    await interaction.response.send_message(f"🎲 ランダムに `{choice[:-4]}` を再生します。")

@bot.tree.command(name="shuffleplay", description="全曲をランダム順に再生します。")
async def shuffleplay(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    music_dir = "./music"
    files = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
    if not files:
        await interaction.response.send_message("❌ 曲が見つかりません。")
        return

    random.shuffle(files)
    for f in files:
        music_queues[guild_id].append(os.path.join(music_dir, f))

    await interaction.response.send_message("🔀 全曲をランダム順にキューに追加しました。")

    vc = interaction.guild.voice_client
    if vc is None or not vc.is_connected():
        if interaction.user.voice and interaction.user.voice.channel:
            vc = await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("❗️ボイスチャンネルに参加してください。", ephemeral=True)
            return

    if not vc.is_playing():
        play_next(interaction.guild, vc)


@bot.command()
async def test(ctx):
    embed = discord.Embed(title="正常に動作しています。", color=discord.Colour.purple())
    await ctx.send(embed=embed)

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
            {"id": 84, "name": "コラプス", "color": 0x8a57fb, "type": "オリジナル", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/1077032367719469117/1289240154309136445/F7F9E844-4FCB-4E4C-8579-487DD43A6B28.jpg"}
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

@bot.event
async def on_message(message):
    global model_engine
    if message.author.bot:
        return
    if message.author == bot.user:
        return

    # メンションに反応
    if bot.user in message.mentions:
        try:
            # プロンプトをそのまま使用
            prompt = message.content.strip()
            if not prompt:
                await message.channel.send("質問内容がありません")
                return
            
            # OpenAIのChat APIを使用して応答を生成
            completion = openai.ChatCompletion.create(
                model=model_engine,
                messages=[
                    {
                        "role": "system",
                        "content": "送られてきた文章に対して優しく返信してください。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )

            response = completion.choices[0].message['content']
            await message.channel.send(response)
        except openai.error.RateLimitError:
            await message.channel.send("現在のAPI使用量制限を超えています。プランのアップグレードや使用量の確認を行ってください。")
        except Exception as e:
            import traceback
            traceback.print_exc()
            await message.channel.send("エラーが発生しました。")

bot.run(TOKEN)