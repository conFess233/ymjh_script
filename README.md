# 基于python的一梦江湖脚本
> 本脚本基于python编写，用于自动完成一梦江湖中的任务流程。<br>
> 一个学习项目，慢慢写着玩~

## 使用方法
>这个脚本目前仅支持windows的一梦江湖pc端

>建议直接下载打包版，即开即用。https://github.com/conFess233/ymjh_script/releases

1. [安装python环境](https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe)

2. 克隆仓库或下载源码
```
git clone https://github.com/conFess233/ymjh_script.git
```
>或者直接下载源码: https://github.com/conFess233/ymjh_script/archive/refs/heads/main.zip

>以下操作建议使用Powershell(管理员)或cmd(管理员)进行，否则百分百会出问题
><br>如果使用vscode, PyCharm等, 用管理员权限打开即可。
3. 进入项目目录
```
cd 你的项目路径/ymjh_script
```

4. 环境配置(这里推荐使用虚拟环境)
>创建虚拟环境
```
python -m venv venv
```
>激活虚拟环境
```
venv\Scripts\activate
```
>退出虚拟环境(如有需要)
```
deactivate
```

5. 安装依赖
```
pip install -r requirements.txt
```

6. 运行脚本
```
python main.py
```
>另一种方法，打包后直接运行，首先需要安装pyinstaller
```
pip install pyinstaller
```
>然后在项目根目录(ymjh_script)下运行以下命令进行打包。<br>注意，upx-dir参数需要根据实际情况修改。<br>upx是一个压缩工具，用于压缩生成的exe文件，减小文件大小。懒得搞可以不使用。
```
pyinstaller -F -w --clean --upx-dir D:\code\upx-5.0.2-win64\ main.py --add-data "src/ui/core/styles.qss.template:."
```
>不使用upx压缩的命令如下
```
pyinstaller -F -w --clean main.py --add-data "src/ui/core/styles.qss.template:."
```
>打包后会项目根目录的dist目录下生成一个main.exe文件，将项目根目录的template_img/复制到dist目录下，以管理员运行main.exe即可。
>> 打包后的main.exe文件运行需要读取template_img/目录，否则无法加载模板，只要确保程序启动时template_img/目录和main.exe在相同目录下即可。

## 注意事项
- 使用本脚本不确定会不会封号，请谨慎使用。
>反正我还没被封（
- 运行脚本时请确保一梦江湖客户端已经登录并且在主界面。
- 如果脚本无法正常运行，请检查系统缩放，一般为125%。
- 脚本运行时可操作其它窗口，但不要将游戏窗口最小化，这会导致系统停止渲染游戏画面，导致脚本无法正常运行。
- 点击间隔尽量设置在1.5秒以上，以免因游戏ui的淡入淡出动画导致点击无效。

## 预定添加的功能
- [x] 暂停
- [x] 多开
- [ ] 更多任务流程
- [x] 资源占用优化
- [ ] 更准确的匹配方法

## 已实现的任务流程
- 日常副本
- 论剑

## 已知问题
- ~~在进行日常副本挂机时，可能会因为场景过暗导致无法匹配到退出按钮而卡住的情况。（已修复）~~

## 更新日志
- *2025-12-04* 实现了暂停功能，增加了任务计时，每轮任务完成后显示耗时，添加一些使用说明。
- *2025-12-05* 增加了多开功能，日志自动保存功能。修改了部分日志的输出方式，现在在ui界面显示的日志不会太过冗长，只显示必要的信息。
- *2025-12-11* 放弃使用多进程实现多开，改为多线程，限制日志行数，以防日志过多导致内存泄漏。
- *2025-12-14* 更换了一些模板，修复了一些匹配错误的情况。增加简单的防检测机制（点击位置随机偏移+随机截图/点击间隔）。创建任务时直接将其内模板全部初始化到内存，避免了每次匹配时都需要读取模板文件的情况。修改截图方法为BitBlt，提高截图效率。
- *2025-12-17* 优化任务流程，新增状态机机制，更容易扩展任务流程，修改了部分模板。
- *2025-12-19* 解耦taskModel，提高一些可扩展性，新增了一些信号槽机制，方便在ui界面进行操作。