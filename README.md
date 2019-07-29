# WeiBoSpider

1. 简介

   一个基于 python3.6.8 和 [splinter](https://github.com/cobrateam/splinter)  的微博爬虫，可以爬取指定日期之间的微博信息。

2. 使用

   - 前提，电脑以安装 Firefox 浏览器，系统为 windows；要想使用 Chrome，则只需要修改 WeiSpider 类中的 driver_path 为 ` "../driver/chromedriver.exe" ` 即可。
   - 在 requirements.txt 同级目录下，使用命令`pip install -r requirements.txt`安装项目依赖包。
   - 最后在 src 目录下之间使用 python weibo.py 即可运行项目，然后按照控制台输出信息进行操作即可。
   - 提示：在 weibo.py 的 main() 方法中，可以设置微博登录信息，用户名和密码，运行时可以自动填充，登录时只需手动输入验证码即可。

3. 优点

   在爬取数据过程中，如果感觉爬取时间过长，可以按下 CTRL + C 结束爬取，已爬取的内容仍会被保存下来。**只有使用 cmd 运行文件才可以实现。**