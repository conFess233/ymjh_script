# 基于python的一梦江湖脚本
> 本脚本基于python编写，用于自动完成一梦江湖中的任务流程。<br>
> 一个学习项目，慢慢写着玩~

## 使用方法
>这个脚本目前仅支持windows的一梦江湖pc端

1. 安装python环境
>https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe

2. 克隆仓库或下载源码
```
git clone https://github.com/conFess233/ymjh_script.git
```
>或者直接下载zip文件并解压: https://github.com/conFess233/ymjh_script/archive/refs/heads/main.zip

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
>打包后会项目根目录的dist目录下生成一个main.exe文件，将项目根目录的template_img文件夹复制到dist目录下，以管理员运行main.exe即可。
>> 打包后的main.exe文件运行需要template_img文件夹，否则无法加载模板，只要确保template_img文件夹在和main.exe在相同目录下即可。

## 注意事项
- 使用本脚本不确定会不会封号，请谨慎使用。
>反正我还没被封（
- 运行脚本时请确保一梦江湖客户端已经登录并且在主界面。
- 如果脚本无法正常运行，请检查系统缩放，一般为125%。
- 脚本运行时可操作其它窗口，但不要将游戏窗口最小化，这会导致系统停止渲染游戏画面，导致脚本无法正常运行。
- 目前多开功能还没有经过测试，可能会出现一些问题。

## 预定添加的功能
- <input type="checkbox" checked="true" disabled="true">暂停</input>
- <input type="checkbox" checked="true" disabled="true">多开</input>
- <input type="checkbox" disabled="true">更多任务流程</input>
- <input type="checkbox" disabled="true">资源占用优化</input>
- <input type="checkbox" disabled="true">更准确的匹配方法</input>

## 已实现的任务流程
- 日常副本
- 论剑

## 更新日志
- *2025-12-04* 实现了暂停功能，增加了任务计时，每轮任务完成后显示耗时，添加一些使用说明。
- *2025-12-05* 增加了多开功能，日志自动保存功能。修改了部分日志的输出方式，现在在ui界面显示的日志不会太过冗长，只显示必要的信息。
>多开使用多进程实现，每个进程独立运行，互不干扰。
><br>通过管道(pipe)与队列(queue)实现子进程与主进程的通信，子进程将任务结果发送给主进程，主进程通过轮询队列，将结果显示在ui界面上，任务列表由ipc线程异步处理。
><br>优点是可以同时运行多个任务流程，每个任务流程独立运行，互不干扰。
><br>缺点是每个进程占用的资源(内存、cpu等)会增加，同时也会增加系统的负载。实测多创建一个进程会占用40MB左右的内存。
><br>但毕竟只是个小脚本，应该没关系吧(￣▽￣)~*