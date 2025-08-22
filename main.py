import discord, os, random, asyncio, datetime, pytz, openai, aiohttp, gspread, pytesseract, json, firebase_admin, re
from discord.ext import commands, tasks
from discord import app_commands, ui, Embed, Color
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
from datetime import datetime, timezone, timedelta
load_dotenv()

# 別ファイルで管理
from data.heroes import heroes
from cogs.stage import get_file_stage
from cogs.omikuji import draw_omikuji

# Koyeb用 サーバー立ち上げ
import uvicorn
from server import app

# TOKEN = os.getenv('kani_TOKEN')  # 🦀bot
TOKEN = os.getenv('cps_TOKEN')  # カスタム大会bot
PORT = int(os.getenv('PORT', 8080))

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
        japan_timezone = timezone(timedelta(hours=9))  # JST (UTC+9)
        now = datetime.now(japan_timezone)  # 修正後
        login_message = f"{now.strftime('%Y年%m月%d日 %H:%M:%S')} ログインしました"
        await target_channel.send(login_message)
    else:
        print("指定されたチャンネルが見つかりません。")

    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}個のコマンドを同期しました。")
    except Exception as e:
        print(e)

    if not check_for_updates.is_running():
        check_for_updates.start()
        print("スプレッドシート監視ループを開始しました")

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

@bot.tree.command(name="おみくじ", description="運勢を占ってくれるよ。")
async def おみくじ(interaction: discord.Interaction):
    await draw_omikuji(interaction)

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

@bot.tree.command(name="ステージ",description="ランダムでステージを表示")
async def ステージ(interacion: discord.Interaction):
    file = get_file_stage()
    await interacion.response.send_message(file=file)

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
    if dice[0] == dice[1] == dice[2]:  # アラシ（ゾロ目）
        return 110 if dice[0] == 1 else 100 - (6 - dice[0])  # ピンゾロ（1,1,1）が最強（110）
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
    kanji_dict = {
        "十": 10, "百": 100, "千": 1000,
        "万": 10000, "億": 100000000, "兆": 1000000000000
    }

    num = 0  # 最終的な数値
    temp = 0  # 一時的な数値（十・百・千）
    section_total = 0  # 「万」「億」単位での合計
    last_unit = 1  # 直前の単位（万・億など）
    has_digit = False  # 数字が出現したか

    # 半角変換（全角→半角）
    text = re.sub(r"(\d+)", lambda m: str(int(m.group(1))), text)

    for char in text:
        if char.isdigit():
            temp = temp * 10 + int(char)  # 数字が続く場合
            has_digit = True
        elif char in kanji_dict:
            unit = kanji_dict[char]
            if unit >= 10000:  # 「万」以上の単位が出たら
                if temp == 0 and not has_digit:
                    temp = 1  # 例: 「万」だけの時は 1万

                section_total += temp * last_unit
                num += section_total * unit
                section_total = 0  # セクションリセット
                last_unit = unit
                temp = 0
            else:
                if temp == 0:
                    temp = 1  # 例: 「十万」のように前に数字がない場合
                section_total += temp * unit
                temp = 0
        else:
            return None  # 無効な文字が含まれている場合

    num += section_total + temp  # 最後の値を加算
    return num

def load_vip_users():
    vip_users = {}
    docs = db.collection("vip_users").stream()
    for doc in docs:
        data = doc.to_dict()
        expiry_date = data.get("expiry_date")
        if expiry_date:
            vip_users[doc.id] = datetime.fromisoformat(expiry_date)  # ISOフォーマットから日時を取得
    return vip_users

def save_vip_users(vip_users):
    for user_id, expiry_date in vip_users.items():
        db.collection("vip_users").document(user_id).set({"expiry_date": expiry_date.isoformat()})  # ISO形式で保存

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

        if str(self.bot.user.id) in manual_dice_rolls:
            dice = manual_dice_rolls.pop(str(self.bot.user.id))
            result_message, multiplier = get_vs_result(dice)
            strength = get_strength(dice)
            self.dice_result[self.bot.user.id] = (dice, result_message, multiplier, strength)
        else:
            while attempts < max_attempts:
                dice = [random.randint(1, 6) for _ in range(3)]
                result_message, multiplier = get_vs_result(dice)
                strength = get_strength(dice)

                self.dice_result[self.bot.user.id] = (dice, result_message, multiplier, strength)

                if result_message == "目なし":
                    attempts += 1
                    if attempts < max_attempts:
                        continue
                break  # 目なしでない or 3回振り終えたら終了

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
            await interaction.response.send_message(f"すでに掛け金 {format(self.bet_amount, ',')} {CURRENCY} が設定されています。", ephemeral=True)
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

            if bet_amount is None or bet_amount <= 0 or bet_amount > balances.get(str(self.user1.id), 0):
                await interaction.followup.send("無効な掛け金です。所持金の範囲内で正しい数字を入力してください。", ephemeral=True)
                self.betting_in_progress = False  # 入力失敗時にフラグをリセット
                return

            self.bet_amount = bet_amount
            await interaction.followup.send(f"掛け金を {format(self.bet_amount, ',')} {CURRENCY} に設定しました！")

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

        now = datetime.utcnow()
        vip_users = load_vip_users()

        if user1_strength == user2_strength:
            result_embed = discord.Embed(
                title="対戦結果",
                description=f"引き分け！\n"
                            f"{self.user1.mention} の所持金: {format(balances.get(str(self.user1.id), 0), ',')}{CURRENCY}\n"
                            f"{self.user2.mention} の所持金: {format(balances.get(str(self.user2.id), 0), ',')}{CURRENCY}",
                color=discord.Color.gold()
            )
            await self.show_bot_dice_result(interaction)
            await interaction.followup.send(embed=result_embed)
            self.disable_buttons()
            self.game_over = True
            return

        winner = self.user1 if user1_strength > user2_strength else self.user2
        loser = self.user2 if winner == self.user1 else self.user1

        is_winner_vip = str(winner.id) in vip_users and vip_users[str(winner.id)] > now
        is_loser_vip = str(loser.id) in vip_users and vip_users[str(loser.id)] > now

        winner_multiplier = self.dice_result[winner.id][2]
        loser_multiplier = self.dice_result[loser.id][2]

        if loser_multiplier == -2:
            adjusted_multiplier = abs(winner_multiplier) * 2
        else:
            adjusted_multiplier = abs(winner_multiplier)

        base_amount_won = self.bet_amount * adjusted_multiplier
        bonus_multiplier = random.choice([1.05, 1.10]) if is_winner_vip else 1.0
        amount_won = int(base_amount_won * bonus_multiplier)

        base_loss = self.bet_amount * adjusted_multiplier
        VIP_LOSS_REDUCTION = 0.10  # 10% 還元
        amount_lost = int(base_loss * (1 - VIP_LOSS_REDUCTION)) if is_loser_vip else base_loss

        if winner.id != self.bot.user.id:
            balances[str(winner.id)] += amount_won
        if loser.id != self.bot.user.id:
            balances[str(loser.id)] -= amount_lost
        if winner.id == self.bot.user.id:
            balances[str(self.bot.user.id)] += amount_won

        if winner.id != self.bot.user.id or loser.id != self.bot.user.id:
            save_balances(balances, debts)

        winner_name = f"👑 {winner.mention}" if is_winner_vip else winner.mention
        loser_name = f"👑 {loser.mention}" if is_loser_vip else loser.mention

        if is_winner_vip:
            increase_percent = int((bonus_multiplier - 1) * 100)
            bonus_detail = f"\n（VIPボーナス{increase_percent}% で {format(base_amount_won, ',')}{CURRENCY} → {format(amount_won, ',')}{CURRENCY}）"
        else:
            bonus_detail = ""

        result_embed = discord.Embed(
            title="対戦結果",
            description=f"{winner_name} 勝利！\n"
                        f"掛け金 {format(self.bet_amount, ',')}{CURRENCY} の **{adjusted_multiplier} 倍** で "
                        f"**{format(amount_won, ',')}{CURRENCY} 獲得** {bonus_detail}\n"
                        f"{loser_name} は **{format(amount_lost, ',')}{CURRENCY} 失いました**\n"
                        f"{self.user1.mention} の所持金: {format(balances.get(str(self.user1.id), 0), ',')}{CURRENCY}\n"
                        f"{self.user2.mention} の所持金: {format(balances.get(str(self.user2.id), 0), ',')}{CURRENCY}",
            color=discord.Color.gold()
        )


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
    vip_users = load_vip_users()
    now = datetime.utcnow()

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

        balance_text = f"{format(balance, ',')} {CURRENCY}"
        if debt_amount > 0:
            balance_text += f" (借金: {format(debt_amount, ',')} {CURRENCY})"

        # VIPなら👑をつける
        if uid in vip_users and vip_users[uid] > now:
            user_display = f"👑 {user_display}"

        rank += 1

        if displayed_count < 10:
            embed.add_field(
                name=f"{rank}位 {user_display}",
                value=f"総資産: **{format(net_worth, ',')} {CURRENCY}**\n{balance_text}",
                inline=False
            )
            displayed_count += 1

        if uid == user_id:
            user_rank = rank
            user_balance_text = f"総資産: **{format(net_worth, ',')} {CURRENCY}**\n{balance_text}"

    if user_rank and user_rank > 10:
        embed.add_field(
            name="あなたの順位",
            value=f"{user_rank}位 {interaction.user.mention}\n{user_balance_text}",
            inline=False
        )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="所持金", description="自分の所持金を表示")
async def 所持金(interaction: discord.Interaction):
    balances, debts = load_balances()
    vip_users = load_vip_users()
    user_id = str(interaction.user.id)
    now = datetime.utcnow()

    balance = balances.get(user_id, 0)
    debt_amount = debts.get(user_id, 0)

    balance_text = f"{format(balance, ',')} {CURRENCY}"
    if debt_amount > 0:
        balance_text += f" (借金: {format(debt_amount, ',')} {CURRENCY})"

    # VIPなら👑をつける
    user_display = f"👑 {interaction.user.mention}" if user_id in vip_users and vip_users[user_id] > now else interaction.user.mention

    embed = discord.Embed(
        title=f"{user_display} の所持金",
        description=balance_text,
        color=discord.Color.purple()
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="借金", description="最大5万ずつ借金可能")
async def 借金(interaction: discord.Interaction, amount: str):
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)
    admin_ids = ["513153492165197835", "698894367225544735"]

    amount = re.sub(r'[^\d十百千万億兆]', '', amount)
    amount = kanji2num(amount) if not amount.isdigit() else int(amount)

    if amount is None or amount <= 0:
        await interaction.followup.send("無効な借金額です。半角数字または漢数字で入力してください。", ephemeral=True)
        return

    ensure_balance(user_id)

    vip_users = load_vip_users()
    now = datetime.utcnow()
    max_allowed_loan = 50000
    if str(user_id) in vip_users and vip_users[str(user_id)] > now:
        max_allowed_loan = 10000000

    if user_id not in admin_ids and amount > max_allowed_loan:
        await interaction.followup.send(f"1回の借金は最大 {format(max_allowed_loan, ',')} {CURRENCY} までです。", ephemeral=True)
        return

    balances, debts = load_balances()

    if balances[user_id] < 0:
        required_amount = 50000 - balances[user_id]
        debts[user_id] += required_amount
        balances[user_id] = amount
    else:
        debts[user_id] += amount
        balances[user_id] += amount

    save_balances(balances, debts)

    embed = discord.Embed(
        title="借金完了",
        description=f"{interaction.user.mention} は **{format(amount, ',')} {CURRENCY}** 借りました。\n"
                    f"**現在の所持金:** {format(balances[user_id], ',')} {CURRENCY}\n"
                    f"**現在の借金:** {format(debts[user_id], ',')} {CURRENCY}",
        color=discord.Color.red()
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

class RepayDebtView(ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=60)  # 60秒で無効化
        self.interaction = interaction

    @ui.button(label="全額返済", style=discord.ButtonStyle.success)
    async def full_repayment(self, interaction: discord.Interaction, button: ui.Button):
        await repay_debt(interaction, "all")

async def repay_debt(interaction: discord.Interaction, amount: str):
    await interaction.response.defer(ephemeral=True)

    user_id = str(interaction.user.id)

    # Firestore からデータ取得
    balances, debts = load_balances()

    current_debt = debts.get(user_id, 0)  # 借金額を取得
    if current_debt == 0:
        await interaction.followup.send("借金はありません！", ephemeral=True)
        return

    # 'all' が指定された場合、全額返済
    if amount.lower() == "all":
        repayment_amount = min(current_debt, balances[user_id])  # 借金額 or 所持金のどちらか少ない方
    else:
        try:
            repayment_amount = int(amount)
        except ValueError:
            await interaction.followup.send("無効な返済額です。数値を入力するか 'all' を指定してください。", ephemeral=True)
            return

    if repayment_amount <= 0:
        await interaction.followup.send("返済額は正の数を入力してください。", ephemeral=True)
        return

    if repayment_amount > balances[user_id]:
        await interaction.followup.send("所持金が足りないため、借金を返済できません。", ephemeral=True)
        return

    # 返済処理
    debts[user_id] -= repayment_amount
    balances[user_id] -= repayment_amount  # 所持金から減らす

    # Firestore に保存
    save_balances(balances, debts)

    embed = discord.Embed(
        title="借金返済",
        description=f"{interaction.user.mention} は **{format(repayment_amount, ',')} {CURRENCY}** 返済しました。\n"
                    f"**現在の所持金:** {format(balances[user_id], ',')} {CURRENCY}\n"
                    f"**残りの借金:** {format(debts[user_id], ',')} {CURRENCY}",
        color=discord.Color.green()
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="借金返済", description="借金を返済できます（'all' で全額返済）")
async def 借金返済(interaction: discord.Interaction, amount: str = ""):
    if amount == "":
        # ボタン付きのメニューを表示
        view = RepayDebtView(interaction)
        await interaction.response.send_message("借金返済メニュー", view=view, ephemeral=True)
    else:
        await repay_debt(interaction, amount)

VIP_COST = 10000000  # VIP加入費用（1000万）
VIP_DURATION = timedelta(weeks=1)  # VIPの期間（1週間）
VIP_BONUS_MIN = 0.05  # 勝利時のボーナス最小値（+5%）
VIP_BONUS_MAX = 0.10  # 勝利時のボーナス最大値（+10%）
VIP_LOSS_REDUCTION = 0.10  # 敗北時の損失軽減（10%還元）

class VIPView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.interaction = None  # インタラクションを保存するための変数

    async def on_timeout(self):
        """30秒経過したらキャンセルメッセージを送る"""
        if self.interaction:
            try:
                await self.interaction.followup.send("30秒経過したためVIP加入をキャンセルしました。", ephemeral=True)
            except discord.HTTPException:
                pass  # インタラクションがすでに終了していた場合は無視

    @ui.button(label="VIPに加入する", style=discord.ButtonStyle.green)
    async def join_vip(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        now = datetime.utcnow()

        vip_users = load_vip_users()  # Firestore から VIP 情報をロード

        if user_id in vip_users and vip_users[user_id] > now:
            await interaction.response.send_message("あなたはすでにVIPです！", ephemeral=True)
            return
        
        balances, debts = load_balances()

        if balances.get(user_id, 0) < VIP_COST:
            await interaction.response.send_message(f"VIP加入には **{format(VIP_COST, ',')} {CURRENCY}** 必要です。所持金が足りません。", ephemeral=True)
            return

        # VIP料金を差し引く
        balances[user_id] -= VIP_COST
        vip_users[user_id] = now + VIP_DURATION  # VIP期間を1週間に設定
        save_balances(balances, debts)  # Firestore に保存
        save_vip_users(vip_users)  # VIP情報も保存

        japan_timezone = timezone(timedelta(hours=9))  # JST (UTC+9)
        expiry_date_jst = vip_users[user_id].astimezone(japan_timezone)

        embed = Embed(
            title="VIP 加入完了！",
            description=f"{interaction.user.mention} は **VIP** になりました！\n"
                        f"**特典**:\n"
                        f"**勝利時** : 獲得コイン +5%～10% ボーナス\n"
                        f"**敗北時** : 10% のコインが戻る\n"
                        f"**VIP有効期限:** {expiry_date_jst.strftime('%Y年%m月%d日 %H時%M分')} JST",
            color=Color.gold()
        )

        await interaction.response.edit_message(content="VIP加入が完了しました！", embed=embed, view=None)
        self.stop()  # ボタンの無効化

    @ui.button(label="キャンセル", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="VIP加入をキャンセルしました。", view=None)
        self.stop()  # ボタンの無効化

@bot.tree.command(name="vip加入", description="VIPに加入するための確認画面を表示")
async def vip加入(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    vip_users = load_vip_users()
    now = datetime.utcnow()

    if user_id in vip_users and vip_users[user_id] > now:
        await interaction.response.send_message("あなたはすでにVIPです！", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    embed = Embed(
        title="VIPメンバーシップ加入確認",
        description=f"VIPに加入すると、**{format(VIP_COST, ',')} {CURRENCY}** を支払い、特別な特典を受け取ることができます！\n\n"
                    "**VIP特典一覧**\n"
                    "**勝利時ボーナス** : 獲得コインが **+5%or10%** アップ！\n"
                    "**敗北時補償** : 失ったコインの **10%** が戻ってくる！\n"
                    "**借金上限** :借金上限が5万から1000万になる!\n"
                    "**VIPバッジ** : ランキングや結果画面で **👑マーク** が付く！\n\n"
                    "**VIP期間:** 1週間\n\n"
                    "本当にVIPに加入しますか？",
        color=Color.gold()
    )

    view = VIPView(user_id)
    view.interaction = interaction
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="vip期間", description="現在のVIP期間を確認")
async def vip期間(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    now = datetime.utcnow()

    vip_users = load_vip_users()

    if user_id not in vip_users or vip_users[user_id] < now:
        await interaction.response.send_message("あなたはVIPではありません。", ephemeral=True)
        return

    remaining_days = (vip_users[user_id] - now).days

    japan_timezone = timezone(timedelta(hours=9))  # JST (UTC+9)
    expiry_date_jst = vip_users[user_id].astimezone(japan_timezone)

    embed = Embed(
        title="VIPステータス",
        description=f"**VIP有効期限:** {expiry_date_jst.strftime('%Y年%m月%d日 %H時%M分')}\n"
                    f"**残り日数:** {remaining_days}日",
        color=Color.blue()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

class VIPExtensionView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.interaction = None

    async def on_timeout(self):
        if self.interaction:
            try:
                await self.interaction.followup.send("30秒経過したためVIP延長をキャンセルしました。", ephemeral=True)
            except discord.HTTPException:
                pass  # インタラクションが終了していた場合は無視

    @ui.button(label="VIPを延長する", style=discord.ButtonStyle.green)
    async def extend_vip(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        now = datetime.utcnow()

        vip_users = load_vip_users()  # Firestore から VIP 情報をロード

        if user_id not in vip_users or vip_users[user_id] < now:
            await interaction.response.send_message("あなたは現在VIPではありません。先に `/vip加入` してください。", ephemeral=True)
            return

        balances, debts = load_balances()

        if balances.get(user_id, 0) < VIP_COST:
            await interaction.response.send_message(f"VIP延長には **{format(VIP_COST, ',')} {CURRENCY}** 必要です。所持金が足りません。", ephemeral=True)
            return

        balances[user_id] -= VIP_COST
        vip_users[user_id] += VIP_DURATION
        save_balances(balances, debts)
        save_vip_users(vip_users)

        japan_timezone = timezone(timedelta(hours=9))  # JST (UTC+9)
        expiry_date_jst = vip_users[user_id].astimezone(japan_timezone)

        embed = Embed(
            title="VIP延長完了",
            description=f"{interaction.user.mention} の VIP 期間が **1週間延長** されました！\n"
                        f"**新しい有効期限:** {expiry_date_jst.strftime('%Y年%m月%d日 %H時%M分')} JST",
            color=Color.gold()
        )

        await interaction.response.edit_message(content="VIP延長が完了しました！", embed=embed, view=None)
        self.stop()  # ボタンの無効化

    @ui.button(label="キャンセル", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="VIP延長をキャンセルしました。", view=None)
        self.stop()  # ボタンの無効化

@bot.tree.command(name="vip延長", description="VIPの期間を延長する")
async def vip延長(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    vip_users = load_vip_users()  # FirestoreからVIPデータを取得
    now = datetime.utcnow()

    if user_id not in vip_users or vip_users[user_id] < now:
        await interaction.response.send_message("あなたは現在VIPではありません。先に `/vip加入` してください。", ephemeral=True)
        return

    embed = Embed(
        title="VIP延長確認",
        description=f"VIPを延長すると **{format(VIP_COST, ',')} {CURRENCY}** を支払います。\n"
                    "VIP期間は **1週間延長** されます。\n"
                    "本当に延長しますか？",
        color=Color.orange()
    )

    view = VIPExtensionView(user_id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    view.interaction = interaction  # インタラクションを保存

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

@bot.command(name="BOT出目設定")
async def BOT出目設定(ctx, *, dice_input: str):
    admin_ids = ["513153492165197835", "1075092388835512330"]
    if str(ctx.author.id) not in admin_ids:
        await ctx.send("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    try:
        dice = [int(num) for num in dice_input.split(",")]
        if len(dice) != 3 or any(d < 1 or d > 6 for d in dice):
            raise ValueError

        manual_dice_rolls[str(bot.user.id)] = dice
        await ctx.send(f"BOTの出目を {dice} に設定しました！", ephemeral=True)

    except ValueError:
        await ctx.send("正しい形式で入力してください！ 例: `!BOT出目設定 1,2,3`", ephemeral=True)

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
        self.heroes = heroes
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

# bot.run(TOKEN)

async def start_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    # サーバーと bot を同時に起動
    await asyncio.gather(
        start_server(),
        bot.start(TOKEN)
    )

if __name__ == "__main__":
    asyncio.run(main())