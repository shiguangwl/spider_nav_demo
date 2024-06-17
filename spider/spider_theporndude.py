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


# 抓取详情页内的数据
def extractDetailData(link):
    htmlTree = etree.HTML(fetchData(link))
    url = htmlTree.xpath('//span[@data-site-domain]/text()')[0]
    content = etree.tostring(htmlTree.xpath('//div[@data-site-description]')[0], method='html', encoding='unicode')
    thumb_img = htmlTree.xpath('//img[@class="example-thumb-img"]/@src')[0]
    ratingCount = htmlTree.xpath('//*[@id="site-description"]/div[2]/div[2]/div[1]/div[2]/div/div/div[3]/span/text()')[0]

    prosComment = ''
    prosLis = htmlTree.xpath('//*[@id="site-description"]/div[2]/div[2]/div[4]/ul[1]/li')
    for proLi in prosLis:
        prosComment += proLi.xpath('string(.)') + '\n'

    consComment = ''
    consLis = htmlTree.xpath('//*[@id="site-description"]/div[2]/div[2]/div[4]/ul[2]/li')
    for conLi in consLis:
        consComment += conLi.xpath('string(.)') + '\n'

    return {
        "url": url,
        "ratingCount": ratingCount,
        "thumbImg": thumb_img,
        "prosComment": prosComment,
        "consComment": consComment,
        "content": content
    }


# 抓取分类图标数据
iconCssText = ''
def extractCategoryIcon(iconClass):
    global iconCssText
    if iconCssText == '':
        iconCssText = fetchData("https://media.porndudecdn.com/includes/css/main.min.css")
    reText = r"\." + iconClass + r"{background-image:url\(\.\.(.*?)\)}"
    matches = re.finditer(reText, iconCssText)
    for match in matches:
        return "https://media.porndudecdn.com/includes" + match.group(1)


# 抓取分类相关数据
def extractCategoryData(categoryElement):
    # 提取分类名称和描述
    categoryName = categoryElement.xpath('.//h2/a/text()')[0]
    categoryDesc = categoryElement.xpath('.//p[@class="desc"]/text()')[0]
    titleClass = categoryElement.xpath('.//h2/span/@class')[0]
    categoryIcon = extractCategoryIcon(titleClass.split(' ')[1])
    # 提取分类详情中的信息
    categoryDetailTree = etree.HTML(
        fetchData(
            categoryElement.xpath('.//h2/a/@href')[0]
        )
    )
    categorySlogan = categoryDetailTree.xpath('/html/body/div[1]/div[2]/div/div[3]/h1/span[2]/text()')[0]
    categoryContent =etree.tostring(categoryDetailTree.xpath('.//div[contains(@class,"category-desc")]/.')[0],method='html', encoding='unicode')
    # 移除categoryContent最外层div
    categoryContent = re.sub(r'<div class="category-desc">|</div>', '', categoryContent)

    # 提取链接数据项
    dataItems = []
    for linkItem in categoryElement.xpath('.//ul/li'):
        dataItem = {
            "title": linkItem.xpath('string(./a)'),
            "orgin": linkItem.xpath('.//a[contains(@class,"review")]/@href')[0],
            "desc": linkItem.xpath('string(./p)')
        }
        dataItems.append(dataItem)

    # 多线程抓取链接详情页数据
    temp_dict = {}
    max_retries = 5
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_item = {executor.submit(extractDetailData, item['orgin']): item for item in dataItems}
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            for attempt in range(max_retries):
                try:
                    detail = future.result()
                    item.update({
                        'url': detail['url'],
                        'content': detail['content'],
                        'thumbImg': detail['thumbImg']
                    })
                    temp_dict[item['title']] = item
                    print(f"抓取数据成功： {item['title']}  {item['url']}")
                    break
                except Exception as exc:
                    print(f"抓取详情失败: {exc} 尝试次数：{attempt}  {item['title']}  {item['orgin']}")
                    time.sleep(1)

    # 保证最终数据的顺序一致性
    linkList = [temp_dict[item['title']] for item in dataItems]
    return {
        "categoryName": categoryName,
        "categoryDesc": categoryDesc,
        "categoryIcon": categoryIcon,
        "linkList": linkList,
        "categorySlogan": categorySlogan,
        "categoryContent": categoryContent
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
    # 主页html中的数据
    for categoryElement in categoryElements:
        # 分批次,优化内存占用
        jsonStr = json.dumps(
            extractCategoryData(categoryElement),
            ensure_ascii=False, indent=4
        )
        with open(f"./datas/outPornDude-{storgePage}.json", "w", encoding="utf-8") as f:
            f.write(jsonStr)
        print("=========数据存盘===========：" + f"./datas/outPornDude-{storgePage}.json")
        storgePage += 1
    # 加载更多异步数据
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
                        jsonStr = json.dumps(extractCategoryData(categoryElement), ensure_ascii=False, indent=4)
                        with open(f"./datas/outPornDude-{storgePage}.json", "w", encoding="utf-8") as f:
                            f.write(jsonStr)
                        print("=========数据存盘===========" + f"./datas/outPornDude-{storgePage}.json")
                        storgePage += 1


if __name__ == '__main__':
    r = getData()
    # print("获取分类数量：" + str(len(r)))
    # print("获取链接数量：" + str(sum([len(item["linkList"]) for item in r])))
    # jsonStr = json.dumps(r, ensure_ascii=False, indent=4)
    # print(jsonStr)
    # # 写入本地文件  out.json
    # with open("../datas/outPornDude.json", "w", encoding="utf-8") as f:
    #     f.write(jsonStr)
