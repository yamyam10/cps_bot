import discord
import random
import os

def get_file_stage():
    stage_num = random.randint(1, 21)  # 1～21
    stageimg = f"stage{stage_num}.jpg"
    file_path = os.path.join("img", "stage", stageimg)
    
    if not os.path.exists(file_path):
        print("stageエラー")
        return None
    
    return discord.File(fp=file_path, filename=stageimg, spoiler=False)
