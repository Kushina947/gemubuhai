import discord
from discord import app_commands
from discord.ext import tasks
import random
import datetime

import config
from teamclass import Team
from database import PlayerAttendanceDatabase

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

TOKEN = config.TOKEN
DIFF_JST_FROM_UTC = 9

database = PlayerAttendanceDatabase()


@tree.command(name='register', description='出場選手を登録する')
async def register(ctx: discord.Interaction, first_game: str, second_game: str, date: str = None) -> None:
    """出場選手を登録する
    Args:
        first_game (str): 一試合目の出場選手
        second_game (str): 二試合目の出場選手
        date (str, optional): 登録する日付 入力しない場合その日の試合のものとして登録します
    """
    if not date:
        jp_time = datetime.datetime.now(
        datetime.timezone.utc) + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        date: str = jp_time.strftime('%m/%d')
    if not '/' in date:
        await ctx.response.send_message(content='日付の形式が正しくありません mm/ddの形式で入力してください')
        return
    if not ctx.channel.name in [team.channel.name for team in TEAM_LIST]:
        await ctx.response.send_message(content='このチャンネルは登録できません\n各チームのチャンネルで登録してください', ephemeral=True)
        return
    embed = discord.Embed(title='出場選手登録', description=date, color=0x00ff00)
    embed.add_field(name='一試合目', value=first_game, inline=True)
    embed.add_field(name='二試合目', value=second_game, inline=True)
    embed.set_footer(icon_url=ctx.user.avatar, text=ctx.user.display_name)
    embed.timestamp = datetime.datetime.now(
        datetime.timezone.utc)
    await ctx.response.send_message(content='登録しました　当日19時まで変更できます', embed=embed)
    database.register(Team=ctx.channel.name, first_game=first_game, second_game=second_game, date=date)


@tree.command(name='check', description='出場選手を確認する')
async def check(ctx: discord.Interaction):
    """登録されている出場選手を確認する
    """
    await ctx.response.send_message(content='検索中...')
    all_register_list = database.get_team_all_register(Team=ctx.channel.name)
    print(all_register_list)
    if not all_register_list:
        await ctx.edit_original_response(content='登録されている情報はありません')
        return
    for register in all_register_list:
        embed = discord.Embed(title=register[3], description='', color=0x00ff00)
        embed.add_field(name='一試合目', value=register[1], inline=True)
        embed.add_field(name='二試合目', value=register[2], inline=True)
        await ctx.channel.send(embed=embed)
    await ctx.edit_original_response(content='登録されている情報はこちらです')


async def check_register(Team: int, date: str) -> bool:
    """指定した日付の出場選手が登録されているか確認する
    Args:
        Team (int): チーム番号
        date (str): 日付
    Returns:
        bool: 登録されていればTrue、されていなければFalse
    """
    register_tuple = PlayerAttendanceDatabase().get_today(Team=Team, date=date)
    if register_tuple:
        return True
    else:
        return False


async def get_register(Team: str, date: str) -> tuple:
    """指定した日付の出場選手を取得する
    Args:
        Team (str): チーム番号
        date (str): 日付
    Returns:
        tuple: 一試合目、二試合目の出場選手
    """
    return PlayerAttendanceDatabase().get_today(Team=Team, date=date)


async def check_all_register(date: str) -> None:
    """すべてのチームが登録されているか確認する
    Args:
        date (str): 日付
    Returns:
        bool: すべてのチームが登録されていればTrue、されていなければFalse
    """
    for team in TEAM_LIST:
        if not await check_register(team.channel.name, date):
            await team.channel.send(f'{team.role.mention} 本日の出場選手が登録されていません\n20:00までに登録してください')
        else:
            pass


async def send_today_game(date: str):
    """本日の出場選手を送信する
    Args:
        date (str): 日付
    """
    embed = discord.Embed(title='本日の出場選手', description='', color=0x00ff00)
    for team in TEAM_LIST:
        first_game, second_game = await get_register(team.channel.name, date)
        embed.add_field(name=team.role.name, value=f'一試合目: {first_game}\n二試合目: {second_game}', inline=True)
    await ALL_CH.send(embed=embed)


async def dice(lst: list) -> int:
    """サイコロ二つを振る
    プレイヤーのダイスに被りがないようにダイスのリストから選び選ばれた要素を削除する
    Args:
        lst (list): サイコロの目のリスト
    Returns:
        int : サイコロの目
    """
    return lst.pop(random.randint(0, len(lst)-1))


async def send_result_dice() -> None:
    """サイコロの結果を埋め込みに変換して送信する
    """
    for team in TEAM_LIST:
        if not await check_register(team.channel.name, date):
            await ALL_CH.send('Auto dice Error\nすべてのチームの出場選手が登録されていないためダイスを振ることができませんでした\n登録していないチームは登録してください')
            return
        else:
            pass
    dice_list = [i+1 for i in range(100)]
    jp_time = datetime.datetime.now(
        datetime.timezone.utc) + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    date = jp_time.strftime('%m/%d')
    list_of_dict = [{}, {}]
    for i in range(2):
        embed = discord.Embed(title=f'--ダイスの結果({i+1}試合目)--', description=date, color=0x00ff00)
        for team in TEAM_LIST:
            player = database.get_today(Team=team.channel.name, date=date)[i]
            list_of_dict[i][player] = await dice(dice_list)
            embed.add_field(name=f'{team.role.name}', value=f'{player}\nDice {list_of_dict[i][player]}', inline=False)
        await ALL_CH.send(embed=embed)
    embed = discord.Embed(title=f'対戦表', description=date, color=0x00ff00)
    for i in range(2):
        sorted_list = sorted(list_of_dict[i], key=list_of_dict[i].get, reverse=True)
        embed.add_field(name=f'{i+1}試合目', value=f'東家 {sorted_list[0]}\n南家 {sorted_list[1]}\n西家 {sorted_list[2]}\n北家 {sorted_list[3]}', inline=True)
    await ALL_CH.send(embed=embed)


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return
    if message.content == '!test':
        await send_result_dice()


@tasks.loop(seconds=60)
async def loop() -> None:
    # *日本時間に変換
    jp_time = datetime.datetime.now(
        datetime.timezone.utc) + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    date = jp_time.strftime('%m/%d')
    time = jp_time.strftime('%H:%M')

    if time == '19:00':
        await check_all_register(date)

    if time == '20:05':
        await send_today_game(date)


# 起動確認
@client.event
async def on_ready() -> None:
    channel = client.get_channel(1222457963986419722)
    jp_time = datetime.datetime.now(datetime.timezone.utc) + \
        datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    day = jp_time.strftime('%m/%d')
    time = jp_time.strftime('%H:%M')
    if not loop.is_running():
        loop.start()
    # スラッシュコマンドを同期
    await tree.sync()
    await client.change_presence(activity=discord.Game(name='こんにちは'))
    #--global変数の定義
    global guild, TEAM1, TEAM2, ALL_CH, TEAM_LIST
    guild = client.get_guild(1110850705784307712)
    TEAM1 = Team(guild, channel_id=1278321568329764896, role_id=1278338680376918129)
    TEAM2 = Team(guild, channel_id=1278334269386919996, role_id=1278339187342442507)
    TEAM3 = Team(guild, channel_id=1278393327884046389, role_id=1278394557066772580)
    TEAM4 = Team(guild, channel_id=1278393414303481940, role_id=1278394597910777957)
    ALL_CH = client.get_channel(1222457963986419722)
    TEAM_LIST = [TEAM1, TEAM2, TEAM3, TEAM4]
    print('ログインしました')
    await channel.send(f'起動したよ{day} {time}')


client.run(TOKEN)