import discord
import random

def get_file_stage():
    stage = random.randint(0, 18) #0~18
    if stage == 0: #0が出たとき
        stageimg="stage1.jpg"
        file = discord.File(fp="stage/stage1.jpg",filename=stageimg,spoiler=False)
    elif stage == 1:
        stageimg="stage2.jpg"
        file = discord.File(fp="stage/stage2.jpg",filename=stageimg,spoiler=False)
    elif stage == 2:
        stageimg="stage3.jpg"
        file = discord.File(fp="stage/stage3.jpg",filename=stageimg,spoiler=False)
    elif stage == 3:
        stageimg="stage4.jpg"
        file = discord.File(fp="stage/stage4.jpg",filename=stageimg,spoiler=False)    
    elif stage == 4:
        stageimg="stage5.jpg"
        file = discord.File(fp="stage/stage5.jpg",filename=stageimg,spoiler=False)
    elif stage == 5:
        stageimg="stage6.jpg"
        file = discord.File(fp="stage/stage6.jpg",filename=stageimg,spoiler=False)
    elif stage == 6:
        stageimg="stage7.jpg"
        file = discord.File(fp="stage/stage7.jpg",filename=stageimg,spoiler=False)
    elif stage == 7:
        stageimg="stage8.jpg"
        file = discord.File(fp="stage/stage8.jpg",filename=stageimg,spoiler=False)
    elif stage == 8:
        stageimg="stage9.jpg"
        file = discord.File(fp="stage/stage9.jpg",filename=stageimg,spoiler=False)
    elif stage == 9:
        stageimg="stage10.jpg"
        file = discord.File(fp="stage/stage10.jpg",filename=stageimg,spoiler=False)
    elif stage == 10:
        stageimg="stage11.jpg"
        file = discord.File(fp="stage/stage11.jpg",filename=stageimg,spoiler=False)
    elif stage == 11:
        stageimg="stage12.jpg"
        file = discord.File(fp="stage/stage12.jpg",filename=stageimg,spoiler=False)
    elif stage == 12:
        stageimg="stage13.jpg"
        file = discord.File(fp="stage/stage13.jpg",filename=stageimg,spoiler=False)
    elif stage == 13:
        stageimg="stage14.jpg"
        file = discord.File(fp="stage/stage14.jpg",filename=stageimg,spoiler=False)
    elif stage == 14:
        stageimg="stage15.jpg"
        file = discord.File(fp="stage/stage15.jpg",filename=stageimg,spoiler=False)
    elif stage == 15:
        stageimg="stage16.jpg"
        file = discord.File(fp="stage/stage16.jpg",filename=stageimg,spoiler=False)
    elif stage == 16:
        stageimg="stage17.jpg"
        file = discord.File(fp="stage/stage17.jpg",filename=stageimg,spoiler=False)
    elif stage == 17:
        stageimg="stage18.jpg"
        file = discord.File(fp="stage/stage18.jpg",filename=stageimg,spoiler=False)
    elif stage == 18:
        stageimg="stage19.jpg"
        file = discord.File(fp="stage/stage19.jpg",filename=stageimg,spoiler=False)
    elif stage == 19:
        stageimg="stage20.jpg"
        file = discord.File(fp="stage/stage20.jpg",filename=stageimg,spoiler=False)
    elif stage == 20:
        stageimg="stage21.jpg"
        file = discord.File(fp="stage/stage21.jpg",filename=stageimg,spoiler=False)
    else: #それ以外なのでERRORが出た時に処理される
        print("stageエラー")
    return file