import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from lxml import etree


def fetchData(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print("Failed to fetch data from", url)
        return None


def extractDetailData(link):
    htmlTree = etree.HTML(fetchData(link))
    url = htmlTree.xpath('//span[@data-site-domain]/text()')[0]
    content = str(etree.tostring(htmlTree.xpath('//div[@data-site-description]')[0]))[2:-1]
    thumb_img = htmlTree.xpath('//img[@class="example-thumb-img"]/@src')[0]
    return {
        "url": url,
        "thumbImg": thumb_img,
        "content": content
    }


def extractCategoryData(categoryElement):
    categoryName = categoryElement.xpath('.//h2/a/text()')[0]
    categoryDesc = categoryElement.xpath('.//p[@class="desc"]/text()')[0]
    linkList = []

    dataItems = []
    for linkItem in categoryElement.xpath('.//ul/li'):
        dataItem = {
            "title": linkItem.xpath('string(./a)'),
            "orgin": linkItem.xpath('.//a[contains(@class,"review")]/@href')[0],
            "desc": linkItem.xpath('string(./p)')
        }
        dataItems.append(dataItem)

    # Use ThreadPoolExecutor to process the dataItems in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(extractDetailData, item['orgin']): item for item in dataItems}

        for future in as_completed(future_to_item):
            item = future_to_item[future]
            # 重试逻辑
            for i in range(5):
                try:
                    detail = future.result()
                    item['url'] = detail['url']
                    item['content'] = detail['content']
                    item['thumbImg'] = detail['thumbImg']
                    linkList.append(item)
                    print("抓取数据成功： " + item['title'] + "  " + item['url'])
                    break
                except Exception as exc:
                    print(f"抓取详情失败: {exc} 尝试次数：{i}  {item['title']}  {item['orgin']}")
                    # 休眠3秒
                    time.sleep(1)

    return {
        "categoryName": categoryName,
        "categoryDesc": categoryDesc,
        "linkList": linkList
    }


def getData():
    baseUrl = "https://theporndude.com/zh"
    responseText = fetchData(baseUrl)
    if not responseText:
        print("请求主页失败：" + baseUrl)
        return []

    htmlTree = etree.HTML(responseText)
    categoryElements = htmlTree.xpath('//*[@id="main_container"]/div')[:-2]
    storgePage = 0
    rDatas = []
    for categoryElement in categoryElements:
        # rDatas.append(extractCategoryData(categoryElement))
        # 分批次,优化内存占用
        jsonStr = json.dumps(extractCategoryData(categoryElement), ensure_ascii=False, indent=4)
        with open(f"../datas/outPornDude-{storgePage}.json", "w", encoding="utf-8") as f:
            f.write(jsonStr)
        print("=========数据存盘===========：" + f"../datas/outPornDude-{storgePage}.json")
        storgePage += 1
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
                        # rDatas.append(extractCategoryData(categoryElement))
                        jsonStr = json.dumps(extractCategoryData(categoryElement), ensure_ascii=False, indent=4)
                        with open(f"../datas/outPornDude-{storgePage}.json", "w", encoding="utf-8") as f:
                            f.write(jsonStr)
                        print("=========数据存盘===========" + f"../datas/outPornDude-{storgePage}.json")
                        storgePage += 1

    return rDatas


if __name__ == '__main__':
    r = getData()
    # print("获取分类数量：" + str(len(r)))
    # print("获取链接数量：" + str(sum([len(item["linkList"]) for item in r])))
    # jsonStr = json.dumps(r, ensure_ascii=False, indent=4)
    # print(jsonStr)
    # # 写入本地文件  out.json
    # with open("../datas/outPornDude.json", "w", encoding="utf-8") as f:
    #     f.write(jsonStr)
