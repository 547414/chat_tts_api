import os
import pandas as pd
import base64


def test_generate_speakers_pt():
    # 设置目标路径
    output_dir = r"D:\mnt\sdb4\projects\chat_tts_api\backend\speakers"
    os.makedirs(output_dir, exist_ok=True)

    # 读取 CSV 文件
    df = pd.read_csv("evaluation_results.csv", encoding="utf-8")

    # 定义函数：base64 解码为文件
    def base64_to_file(base64_str, output_folder):
        with open(output_folder, "wb") as file:
            file.write(base64.b64decode(base64_str))

    # 遍历每一行生成 .pt 文件
    for _, row in df.iterrows():
        seed_id = row["seed_id"]
        emb_data = row["emb_data"]

        output_path = os.path.join(output_dir, f"{seed_id}.pt")

        try:
            base64_to_file(emb_data, output_path)
            print(f"✅ 成功生成: {output_path}")
        except Exception as e:
            print(f"❌ 失败: {seed_id}, 错误: {e}")
