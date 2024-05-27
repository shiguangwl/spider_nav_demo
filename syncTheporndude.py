import json

from pypinyin import pinyin, Style

from common.Logger import logger
from spider.spider_admin import init, getCategoty, getLinkDescAll, addCategory, addLink


def chinese_to_pinyin(text):
    """
    将中文转换为拼音
    """
    pinyin_list = pinyin(text, style=Style.NORMAL)
    return ''.join([item[0] for item in pinyin_list])

if __name__ == '__main__':
    init('https://zgroup.ai','admin','admin123')
    logger.info("开始同步数据")
    # categorys = getCategoty()
    # logger.info("categorys：" + str(categorys))
    allLinks = getLinkDescAll()
    logger.info("allLinks len：" + str(len(allLinks)))

    # 加载本地json数据
    datas = []
    with open('outPornDude.json', 'r') as file:
        datas = json.load(file)

    # categoryNames = {i['title'] for i in categorys}
    # for item in datas:
    #     # 判断分类是否存在
    #     if item['categoryName'] not in categoryNames:
    #         logger.info("开始创建分类：" + item['categoryName'])
    #         # 创建分类
    #         addCategory(
    #             item['categoryName'],
    #             chinese_to_pinyin(item['categoryName']),
    #             "-1",
    #             item['categoryDesc'],
    #             "",
    #             "",
    #             "",
    #         )

    # # 重新获取分类数据
    # categorys = getCategoty()
    with open('outCategory.json', 'r') as file:
        categorys = json.load(file)

    categoryIds = {i['title']: i['id'] for i in categorys}
    # 同步链接
    for item in datas:
        for link in item['linkList']:
            # 判断链接是否存在
            isExist = False
            for exitedLink in allLinks:
                if link['title'] == exitedLink['title'] and link['categoryName'] == exitedLink['categoryName'] :
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
                )
