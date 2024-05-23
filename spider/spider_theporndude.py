import json
import re

import requests
from lxml import etree

from common.Logger import logger
def fetchData(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print("Failed to fetch data from", url)
        return None

def extractCategoryData(categoryElement):
    categoryName = categoryElement.xpath('.//h2/a/text()')[0]
    categoryDesc = categoryElement.xpath('.//p[@class="desc"]/text()')[0]
    linkList = []
    for linkItem in categoryElement.xpath('.//ul/li'):
        dataItem = {
            "title": linkItem.xpath('string(./a)'),
            "orgin": linkItem.xpath('.//a[contains(@class,"review")]/@href')[0],
            "desc": linkItem.xpath('string(./p)')
        }
        detail = extractDetailData(dataItem['orgin'])
        logger.info("抓取数据成功：" + str(dataItem))
        dataItem['url'] = detail['url']
        dataItem['content'] = detail['content']
        linkList.append(dataItem)
    return {
        "categoryName": categoryName,
        "categoryDesc": categoryDesc,
        "linkList": linkList
    }

def extractDetailData(link):
    htmlTree = etree.HTML(fetchData(link))
    url = htmlTree.xpath('//span[@data-site-domain]/text()')[0]
    content = str(etree.tostring(htmlTree.xpath('//div[@data-site-description]')[0]))[2:-1]
    return {
        "url": url,
        "content": content
    }


#   [
#     {
#         "categoryName": "免费色情视频网站",
#         "categoryDesc": "在世界上最流行的\...",
#         "linkList": [
#             {
#                 "title": "PornHub",
#                 "orgin": "https://theporndude.com/zh/566/pornhub",
#                 "desc": "PornHub.com.",
#                 "url": "https://pornhub.com",
#                 "content": "<div clas</div>"
#             }
#         }
#     ]
def getData():
    baseUrl = "https://theporndude.com/zh"
    responseText = fetchData(baseUrl)
    if not responseText:
        logger.info("请求主页失败：" + baseUrl)

    htmlTree = etree.HTML(responseText)
    categoryElements = htmlTree.xpath('//*[@id="main_container"]/div')[:-2]

    rDatas = []
    for categoryElement in categoryElements:
        rDatas.append(extractCategoryData(categoryElement))

    # 加载更多数据
    pattern = r'https://assets.tpdfiles.com/includes/pi/zh..+.passive.info.js'
    matches = re.finditer(pattern, responseText)
    for match in matches:
        jsText = fetchData(match.group())
        if jsText:
            pattern = 'passive_index_file = (.+);'
            subMatches = re.finditer(pattern, jsText)
            for subMatch in subMatches:
                linkUrl = subMatch.group(1)[1:-1]
                divs = json.loads(fetchData('https://theporndude.com/includes/pi/' + linkUrl))
                for item in divs:
                    categoryHtml = etree.HTML(item)
                    categoryElements = categoryHtml.xpath('//div[contains(@id, "category-block-")]')
                    for categoryElement in categoryElements:
                        rDatas.append(extractCategoryData(categoryElement))

    return rDatas


if __name__ == '__main__':
    r = getData()
    print("获取分类数量：" + str(len(r)))
    print("获取链接数量：" + str(sum([len(item["linkList"]) for item in r])))
    jsonStr = json.dumps(r)
    print(jsonStr)
    # 写入本地文件  out.json
    with open("../outPornDude.json", "w", encoding="utf-8") as f:
        f.write(jsonStr)





