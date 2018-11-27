# AdvancedBuildKit

一个简易的日常构建工具包，支持通过命令行触发freestyle编译，跨gerrit通过关键字快速拉取分支，一键push变更到服务器，一键创建个人分支等快捷命令


### 下载工具包
```shell
# 下载工具包
git clone http://gitlab.xxxx.com/liming1/auto_build_tools.git

# 切换到dev分支
git checkout dev
```

### 安装依赖
工具是用python写的，所以需要安装一些依赖，推荐使用pip：

pip安装见：http://pip-cn.readthedocs.io/en/latest/installing.html

```shell
# ubuntu专用
sudo apt-get install python3-pip
```

安装好之后，使用如下命令安装依赖包（因为只支持python3，所以需要安装到python3的目录下）

```shell
# 一键安装依赖
pip3 install -r requirements.txt
```

### 初始化
```shell
# 初始化
python3 ./setup.py
```

注意事项：
1. 工具包需要邮箱用户名和密码，是为了使用gerrit和jenkins的功能。
2. 如果需要提测单功能，请输入redmineKey，如果不懂这是什么，请回车跳过
3. 初始化结束之后会缓存jenkins的Jobs，耗时大概3-5分钟
4. **用户名与密码存放于工具包configs/.user_profile文件中，密码过期之后直接删掉这个文件即可重置**

### 使用说明

* `perform_build [branch_keyword]` 根据关键字选择分支，输入review链接（回车分割多个，Ctrl-D结束输入）即可触发对应的freestyle构建

* `create_branch [branch_keyword]` 会根据当前所在目录识别git库，然后根据关键字选择基准分支，输入要创建的个人分支即可

* `push_branch [all]` push本地变更到对应的远程分支，不加参数all只能push到gerrit，加all会直接入库

* `fetch_branch [branch_keyword]` 拉取指定关键字的分支，并checkout到以当前时间戳的分支，支持跨gerrit

* `signmodule [-h] [-m {settings,systemuitools,systemui}]` 不加参数，只触发签名操作，指定模块可以触发对应模块签名，然后push到手机指定位置

* `cp2branch [-h] [-f FILE | -b BRANCH] [-t TARGET_FILE]` 可以cherry-pick到指定分支，支持多分支和多个提交，详情见help

* `download_jenkins_log` 下载指定jenkins job日志



### TODO
1.  目前只支持python3，后续兼容python2
2.  只对bash做了支持，后续考虑兼容zsh

有问题欢迎多多吐槽