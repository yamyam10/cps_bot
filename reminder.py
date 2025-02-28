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
            {"id": 15, "name": "ソル=バッドガイ", "color": 0x990c02, "type": "コラボ", "role": "アタッカー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081092479538962483/FF21B5E4-DE3A-430D-896D-8F4D3B7CF769.jpg"},
            {"id": 16, "name": "ディズィー", "color": 0x3acd5c, "type": "コラボ", "role": "ガンナー", "img": "https://cdn.discordapp.com/attachments/688378324342669333/1081092479778029589/6EF61A45-2A9B-45D1-92DC-F5D5A4F9720A.jpg"},
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
