import random
import re
import sys
import time
from collections import OrderedDict
from datetime import datetime

import pandas
from lxml import etree
from splinter.browser import Browser
from splinter.exceptions import ElementDoesNotExist


class Utils:
    @staticmethod
    def get_date(str_time):
        """
        用户格式化传入的时间字符串
        """
        str_time = str_time.strip().replace(' ', '')

        if '今天' in str_time or '分钟前' in str_time or '秒前' in str_time:
            return datetime.now().date()

        str_time = re.findall(r"(.*\d\d月\d\d日).*", str_time)[0]  # 使用正则表达式找出时间

        if "年" not in str_time:
            now_year = datetime.now().year
            str_time = str(now_year) + "年" + str_time

        date = datetime.strptime(str_time, '%Y年%m月%d日')
        return date.date()

    @staticmethod
    def get_num(string):
        """
        用户获取评论数、点赞数等
        """
        number = re.findall(r"(\d+)", string)
        if number:
            return number[0]
        else:
            return '0'


class WeiboSpider(object):
    page_count = 0  # 记录每个页面抓取的数据量
    all_count = 0  # 记录抓取的数据总量
    save_data = OrderedDict({  # 保存抓取的数据
        "昵称": [],
        "微博正文": [],
        "微博链接": [],
        "时间": [],
        "收藏数": [],
        "转发数": [],
        "评论数": [],
        "点赞数": [],
        "设备": []
    })

    xpath_dict = {  # 解析数据用的 xpath
        '昵称': '//div[@class="info"]//a[@class="name"]/text()',
        '微博正文': '//div[@class="content"]/p[@node-type="feed_list_content"]//text()',
        '微博链接': '//div[@class="content"]/p[@class="from"]/a[1]/@href',
        '时间': '//div[@class="content"]/p[@class="from"]/a[1]/text()',
        '收藏数': '//a[@action-type="feed_list_favorite"]/text()',
        '转发数': '//a[@action-type="feed_list_forward"]/text()',
        '评论数': '//a[@action-type="feed_list_comment"]/text()',
        '点赞数': '//div[@class="card-act"]//a[@action-type="feed_list_like"]//em/text()',
        '设备': '//div[@class="content"]/p/a[@rel="nofollow"]/text()'
    }

    def __init__(self, keyword, start_time, end_time, sleep_time=10, username=None, password=None):
        self.username = username  # 微博用户名
        self.password = password  # 微博密码

        self.browser = None
        self.browser_name = "firefox"  # 浏览器名
        self.driver_path = "../driver/firefoxdriver.exe"  # 打开浏览器的驱动

        self.base_url = "https://s.weibo.com/"  # 微博搜索主页
        self.search_url = 'https://s.weibo.com/weibo/{keyword}' \
                          '&timescope=custom:{start_time}:{end_time}&refer=g'  # 搜索结果的url
        self.keyword = keyword  # 搜索关键字
        self.sleep_time = sleep_time  # 点击下一页的时间间隔
        self.start_time = start_time  # 搜索内容的起始时间
        self.end_time = end_time  # 搜索内容的结束时间

        self.base_sava_path = '../files/'  # 输出文件的保存路径
        self.save_file_name = self.keyword + self.start_time + "~" + self.end_time  # 输出文件名

    def refactor_date(self, start_time, end_time):  # 构造搜索的起止时间
        self.start_time = datetime.strptime(start_time, "%Y-%m-%d-%H").strftime("%Y-%m-%d-%H")
        if end_time:
            self.end_time = datetime.strptime(end_time, "%Y-%m-%d-%H").strftime("%Y-%m-%d-%H")
        else:
            self.end_time = datetime.now().strftime('%Y-%m-%d-%H')

    def get_search_url(self):  # 构造搜索url
        self.refactor_date(self.start_time, self.end_time)  # 将输入的时间重构成搜索用的标准参数

        return self.search_url.format(
            keyword=self.keyword, start_time=self.start_time, end_time=self.end_time)

    def login(self):
        """
        用于登录微博
        """
        self.browser = Browser(driver_name=self.browser_name, executable_path=self.driver_path,
                               service_log_path='../files/log.log')  # 打开浏览器

        self.browser.visit(self.base_url)  # 访问微博搜索页面
        self.browser.click_link_by_text('登录')  # 点击登录

        # 填充用户名的密码
        if self.username is not None:
            self.browser.fill("username", self.username)
        if self.password is not None:
            self.browser.fill("password", self.password)

        print("请在打开的浏览器中登录........")

        time.sleep(2)  # 暂停两秒，等待浏览器加载完成
        logining_url = self.browser.url  # 获取正在登录时的 url

        # 防止网络不好时获取不到正在登录时的 url
        while logining_url == self.base_url:
            time.sleep(2)
            logining_url = self.browser.url

        # 通过验证 url 保证已经登录
        while 1:
            if self.browser.url != logining_url:
                break
            time.sleep(2)
        print("已成功登录，开始抓取信息.......")

    def search(self):
        """
        通过构造的搜索 url，跳转到搜索结果页面
        """

        self.browser.visit(self.get_search_url())

    def get_card_data(self, card, xapth_dict: dict):
        """
        用户获取每一篇博客的信息
        """

        etree_html = etree.HTML(card.html)
        number = ['收藏数', '转发数', '评论数', '点赞数']

        self.page_count += 1  # 统计每一页抓取的数据量

        for key in xapth_dict.keys():
            xpath = xapth_dict.get(key)
            data = etree_html.xpath(xpath)

            if data:
                if key in number:
                    self.save_data[key].append(Utils.get_num(data[0]))

                elif key == '时间':
                    self.save_data[key].append(Utils.get_date(data[0]).strftime('%Y-%m-%d'))

                elif key == '微博正文':
                    content = ''.join(data).replace(' ', '').replace('\n', '')
                    self.save_data[key].append(content)

                else:
                    self.save_data[key].append(data[0])

            else:
                if key in number:
                    self.save_data[key].append('0')

                else:
                    self.save_data[key].append('')

    def download_data(self):
        self.browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")  # 跳转到页面底部

        try:
            self.browser.click_link_by_text('查看全部搜索结果')
        except ElementDoesNotExist:
            pass

        page_index = 1  # 记录页码
        while page_index <= 50:  # 微博搜索结果最多为50页

            # 获取真实的页码
            try:
                # 微博搜索结果有时候一直点击下一页，到了最后一页会跳转到第一页
                # 这段代码用于防止出现这种情况
                real_page = re.findall(r'page=(\d+)', self.browser.url)
                if real_page:
                    real_page = int(real_page[0])
                else:
                    real_page = 1
                if real_page < page_index:
                    break

                print('正在抓取第%s页内容：' % page_index, end='')
                self.browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")  # 跳转到页面底部

                cards = self.browser.find_by_xpath('//div[@class="card"]')  # 获取所有的博文

            except KeyboardInterrupt:  # 如果觉得抓取时间过长，可以按下ctrl c 中止抓取，然后可以保存已抓取的信息
                print('中途退出抓取，正则保存中.....')
                break

            for card in cards:  # 遍历所有的文章，获取数据
                try:
                    self.get_card_data(card, self.xpath_dict)
                except KeyboardInterrupt:
                    pass

            try:
                print('本页抓取了%s条数据，模拟等待中.....' % self.page_count)
                self.all_count += self.page_count  # 统计获取的所有数据量
                self.page_count = 0

                # 基于设置的休眠时间，随机设置一个休眠值
                sleep_time = random.randint(self.sleep_time, self.sleep_time + 7)

                time.sleep(sleep_time)  # 模拟用户浏览网页的时间

                try:
                    self.browser.click_link_by_text('下一页')  # 点击下一页
                    page_index += 1

                except ElementDoesNotExist:
                    break

            except KeyboardInterrupt:
                print('中途退出抓取，正则保存中.....')
                break

    def save(self):
        """
        保存数据
        """

        print('--------------------------------------------')
        print('本次共抓取了%s条数据' % self.all_count)

        try:
            data = pandas.DataFrame(self.save_data)
            file_path = self.base_sava_path + self.save_file_name + '.xlsx'

            data.to_excel(file_path, index=False)  # 将数据保存到 excel
            print('文件正在保存...', end='\n\n')

        except Exception as e:
            print('文件保存失败！！！', end='\n\n')
            print(e)

    def close(self):
        self.browser.quit()  # 关闭浏览器

    @staticmethod
    def test():
        """
        用于测试的方法，实际运行时不执行
        """

        browser = Browser(executable_path="../driver/firefox.exe")
        browser.visit(
            "https://s.weibo.com/weibo/%25E5%25B0%25B1%25E5%25"
            "BC%2580%25E5%25A7%258B%25E5%25A4%25A7%25E5%25B9%2585?topnav=1&wvr=6&b=1")

        cards = browser.find_by_xpath('//div[@class="card"]')
        for c in cards:
            etree_html = etree.HTML(c.html)
            a = etree_html.xpath('//div[@class="card-act"]//a[@title="赞"]/em/text()')

            print(a[0])


def main():
    """
    程序运行入口
    """

    print('-----微博数据爬虫-------', end='\n\n')

    # 修改为微博登录信息时，登录时可以自动填充
    username = None
    password = None

    key_word = input('请输入搜索关键字（输入q退出）：')
    if key_word == 'q':
        print("正在退出....")
        sys.exit(0)

    strat_time = input('请输入开始时间（如2017-12-12）：')
    end_time = input('请输入结束时间，不输入默认为直至今日（如2017-12-12）：')
    sleep_time = input('输入两个页面访问间隔时间(默认为10秒)：')

    print('爬取数据正在开始.......')
    print('需要在打开的浏览器中手动登录！', end='\n\n')

    if not sleep_time:
        sleep_time = 10
    else:
        sleep_time = int(sleep_time)

    weibo = WeiboSpider(key_word, strat_time, end_time, sleep_time, username=username, password=password)
    weibo.login()

    while 1:
        weibo.search()
        weibo.download_data()
        weibo.save()

        key_word = input('请输入搜索关键字（输入q退出）：')
        if key_word == 'q':
            print("正在退出......")
            break

        start_time = input('请输入开始时间（如2017-12-12-8 年-月-日-小时）：')
        end_time = input('请输入结束时间，不输入默认为直至现在（如2017-12-12-8 年-月-日-小时）：')

        print('爬取数据正在开始.......')
        weibo.keyword = key_word
        weibo.start_time = start_time
        weibo.end_time = end_time
    weibo.close()


if __name__ == '__main__':
    main()
    # WeiboSpider.test()
