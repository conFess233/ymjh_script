import os


if __name__ == "__main__":
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath("template_img/huo_dong.png"))
    huo_dong_template = {f"{current_dir}\\{t}" for t in {"huo_dong.png", "huo_dong_hong_dian.png"}}
    print(huo_dong_template)