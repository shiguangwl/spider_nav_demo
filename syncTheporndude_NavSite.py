

import json
import os
import re

import requests
from pypinyin import pinyin, Style

from common.Logger import logger
from spider.spider_admin import init, getCategoty, getLinkDescAll, addCategory, addLink


Authorization = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJsb2dpbl91c2VyX2tleSI6ImI4Y2QwMjEyLWNmZDQtNDQ2OS05ZTk0LTljNTM1MDY0YzRhMyJ9.v0vs4WiUQE1U-VxLIiKC1Xxy1RU20M0rESl-k1gSrhCdBt6i01r5swpQ6VN-U-3lF9j9PDa8n5kW-GyHduqRYg"
BaseApi = "http://127.0.0.1:8080"

# 添加分类
def addCategory(
        title: str,
        alias: str,
        description: str,
        categoryShort: str,
        content: str,
        icon: str,
        languageId: int,
        sort: int,
        slogan: str,
        thumb: str
):
    """
    添加分类
    """
    data = {
        "title": title,
        "alias": alias,
        "description": description,
        "descriptionShort": categoryShort,
        "content": content,
        "icon": icon,
        "languageId": languageId,
        "sort": sort,
        "slogan": slogan,
        "thumb": thumb
    }
    # 请求头
    headers = {
        "Authorization": Authorization,
        "Content-Type": "application/json"
    }
    # 请求地址
    url = f"{BaseApi}/navsite/category"
    # 发送请求
    response = requests.post(url, headers=headers, json=data)
    # 返回结果
    return response.json()

# 添加网址
def addLink(
        name: str,
        alias: str,
        description: str,
        content: str,
        keywords: str,
        url: str,
        icon: str,
        preview: str,
        categoryId: int,
        languageId: int,
        sort: int,
        prosComment: str,
        consComment: str,
        flag: str
):
    """
    添加网址
    """
    data = {
        "name": name,
        "alias": alias,
        "description": description,
        "content": content,
        "keywords": keywords,
        "url": url,
        "icon": icon,
        "preview": preview,
        "categoryId": categoryId,
        "languageId": languageId,
        "sort": sort,
        "prosComment": prosComment,
        "consComment": consComment,
        "flag": flag
    }
    # 请求头
    headers = {
        "Authorization": Authorization,
        "Content-Type": "application/json"
    }
    # 请求地址
    url = f"{BaseApi}/navsite/siteInfo"
    # 发送请求
    response = requests.post(url, headers=headers, json=data)
    # 返回结果
    return response.json()


def chinese_to_pinyin(text):
    """
    将中文转换为拼音
    """
    pinyin_list = pinyin(text, style=Style.NORMAL)
    return ''.join([item[0] for item in pinyin_list])



# def testAddCategory():
#     print(addCategory(
#         title="测试分类",
#         alias=chinese_to_pinyin("测试分类"),
#         description="测试分类描述",
#         content="测试分类正文",
#         icon="测试分类图标",
#         languageId=5,
#         sort=0,
#         slogan="测试分类标语"
#     )['data'])

def remove_outer_div(html_string):
    # 使用正则表达式查找最外层的div标签
    pattern = r'^<div[^>]*>(.*?)</div>$'
    match = re.search(pattern, html_string, re.DOTALL)

    if match:
        # 如果找到了最外层的div标签,返回去除div标签后的内容
        return match.group(1)
    else:
        # 如果没有找到最外层的div标签,返回原始字符串
        return html_string


def syncData():
    logger.info("开始同步数据")
    # 加载本地json数据
    datas = []
    # 读取本地datas文件夹中文件数量,确保顺序
    files = os.listdir('./spider/datas')
    for i in range(len(files)):
        # 读取 outPornDude-{i}.json
        try:
            with open(f"./spider/datas/outPornDude-{i}.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                data['linkList'].reverse()
                datas.append(data)
        except Exception as e:
            logger.error(f"读取文件失败: {e}")

    for item in datas:
        # 创建分类
        categoryId = addCategory(
            title=item['categoryName'],
            alias=chinese_to_pinyin(item['categoryName']),
            description=item['categoryDesc'],
            categoryShort=item['categoryShortDesc'],
            content=item['categoryContent'],
            icon=item['categoryIcon'],
            languageId=5,
            sort=0,
            slogan=item['categorySlogan'],
            thumb=item['categoryThumb']
        )
        logger.info("创建分类成功: " + item['categoryName'] + "  " + str(categoryId))
        # 创建分类下链接数据
        item['linkList'].reverse()
        for linkItem in item['linkList']:
            addLink(
                name=linkItem['title'],
                alias=chinese_to_pinyin(linkItem['title']),
                description=linkItem['desc'],
                content=linkItem['content'],
                keywords='',
                url=linkItem['url'],
                icon='',
                preview=linkItem['thumbImg'],
                categoryId=categoryId['data'],
                languageId=5,
                sort=0,
                prosComment=linkItem['prosComment'],
                consComment=linkItem['consComment'],
                flag=linkItem['flag']
            )
            logger.info("创建链接成功: " + linkItem['title'] + "  " + linkItem['url'])




if __name__ == '__main__':
    # testAddCategory()

    syncData()



    # logger.info("开始同步数据")
    #
    # # 加载本地json数据
    # datas = []
    # # 读取本地datas文件夹中文件数量,确保顺序
    # files = os.listdir('./datas')
    # for i in range(len(files)):
    #     # 读取 outPornDude-{i}.json
    #     with open(f"./datas/outPornDude-{i}.json", "r", encoding="utf-8") as f:
    #         data = json.load(f)
    #         data['linkList'].reverse()
    #         datas.append(data)
    #
    # # for item in datas:

