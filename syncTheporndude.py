import json
import os

from pypinyin import pinyin, Style

from common.Logger import logger
from spider.spider_admin import init, getCategoty, getLinkDescAll, addCategory, addLink
from spider.spider_theporndude import getData


def chinese_to_pinyin(text):
    """
    将中文转换为拼音
    """
    pinyin_list = pinyin(text, style=Style.NORMAL)
    return ''.join([item[0] for item in pinyin_list])

if __name__ == '__main__':
    init('http://wuyex.com','admin','admin123')
    logger.info("开始同步数据")
    categorys = getCategoty()
    logger.info("categorys len：" + str(len(categorys)))
    allLinks = getLinkDescAll()
    logger.info("allLinks len：" + str(len(allLinks)))

    # 加载本地json数据
    datas = []
    # 读取本地datas文件夹中文件数量,确保顺序
    files = os.listdir('./datas')
    for i in range(len(files)):
        # 读取 outPornDude-{i}.json
        with open(f"./datas/outPornDude-{i}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            data['linkList'] = data['linkList'].reverse()
            datas.append(data)

    categoryNames = {i['title'] for i in categorys}
    for item in datas:
        # 判断分类是否存在
        if item['categoryName'] not in categoryNames:
            logger.info("开始创建分类：" + item['categoryName'])
            # 创建分类
            addCategory(
                item['categoryName'],
                chinese_to_pinyin(item['categoryName']),
                "-1",
                item['categoryDesc'],
                "",
                "",
                "",
            )

    # 重新获取分类数据
    categorys = getCategoty()
    categoryIds = {i['title']: i['id'] for i in categorys}
    # 同步链接
    for item in datas:
        for link in item['linkList']:
            # 判断链接是否存在
            isExist = False
            for exitedLink in allLinks:
                if link['title'] == exitedLink['title'] and item['categoryName'] == exitedLink['categoryName']:
                    isExist = True
                    break
            if isExist:
                logger.info("链接已存在：" + link['title'])
            else:
                logger.info("开始添加链接：" + link['title'])
                # 创建链接
                addLink(
                    link['title'],
                    link['content'],
                    link['url'],
                    categoryIds[item['categoryName']],
                    link['desc'],
                    '',
                    link['title'],
                    link['title'],
                    link['title'],
                    'https://zgroup.ai/proxy-dGltZWhv/' + link['thumbImg']
                )
