import discord, os, random, asyncio, datetime, pytz, openai, aiohttp, gspread, pytesseract
from discord.ext import commands, tasks
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from discord import ui

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

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)
gspread_client = gspread.authorize(creds)  # gspread用のクライアント

SPREADSHEET_ID = os.getenv('spreadsheet_id')
SHEET_NAME = os.getenv('sheet_name')
CHANNEL_ID = int(os.getenv('channel_id_kani'))

last_row = 0

@bot.event
async def on_ready():
    print(f'ログインしました {bot.user}')

    # メッセージを送信するチャンネルを取得
    target_channel_id = int(os.getenv('channel_id'))
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
async def ダイス(interaction: discord.Interaction):
    view = DiceButton()
    await interaction.response.send_message("サイコロを振りたい場合はボタンを押してね！", view=view)

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