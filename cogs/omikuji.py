import random
import discord

OMIKUJI_RESULTS = [
    ("大吉", 0.05),
    ("吉", 0.25),
    ("中吉", 0.55),
    ("小吉", 0.70),
    ("末吉", 0.95),
    ("大凶", 1.00)
]

async def draw_omikuji(interaction: discord.Interaction):
    """おみくじを引いて結果を送信"""
    result = random.random()
    for title, cumulative_probability in OMIKUJI_RESULTS:
        if result <= cumulative_probability:
            embed = discord.Embed(
                title=f'{interaction.user.mention} さんの運勢は「{title}」です！',
                color=discord.Colour.purple()
            )
            await interaction.response.send_message(embed=embed)
            return
    
    # 通常はここに来ない
    embed = discord.Embed(
        title="ERROR",
        description="運勢の取得中にエラーが発生しました。",
        color=discord.Colour.purple()
    )
    await interaction.response.send_message(embed=embed)
