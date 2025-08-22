import random
import asyncio
import discord

async def team_command(interaction: discord.Interaction, role: discord.Role):
    # ユーザーに応答を返す前に、処理が実行中であることを示す
    await interaction.response.defer()

    # 管理者ロールがない場合は無視
    if not discord.utils.get(interaction.user.roles, name="管理者"):
        await interaction.followup.send(embed=discord.Embed(
            title='このコマンドは管理者のみが実行できます。',
            color=discord.Colour.purple()
        ))
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
        team_role = discord.utils.get(interaction.guild.roles, name=role_name) \
                    or await interaction.guild.create_role(name=role_name, mentionable=True)
        await asyncio.gather(*[member.add_roles(team_role) for member in team])

    # メッセージを一度に送信
    try:
        await interaction.followup.send("\n".join(messages))
        await asyncio.sleep(1)
    except discord.errors.NotFound:
        pass
