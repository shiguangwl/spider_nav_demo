import json
import os
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


# 抓取链接详情页内的数据
def extractDetailData(link):
    htmlTree = etree.HTML(fetchData(link))
    url = htmlTree.xpath('//span[@data-site-domain]/text()')[0]
    content = etree.tostring(htmlTree.xpath('//div[@data-site-description]')[0], method='html', encoding='unicode')
    content = content[
                len('<div class="link-details-review clearfix scrollbox" data-site-description>'):
                -len('</div>')
    ]
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

    # 获取SEO相关字段
    # seoTitle = htmlTree.xpath('/html/head/title/text()')[0]
    # seoDescription = htmlTree.xpath('/html/head/meta[@name="description"]/@content')[0]
    # seoKeywords = htmlTree.xpath('/html/head/meta[@name="keywords"]/@content')[0]

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


# 抓取指定分类的所有站点数据
def extractSiteListByCategoryUrl(categoryUrl):
    htmlText = requests.get(categoryUrl)
    htmlTree = etree.HTML(htmlText.text)
    siteDivList = htmlTree.xpath('//*[@data-site-id]')
    siteList = []
    for siteDiv in siteDivList:
        title = siteDiv.xpath('.//a[@class="link"]/text()')[0].strip()
        orgin = siteDiv.xpath('.//a[@class="link"]/@href')[0]
        try:
            desc = siteDiv.xpath('.//div[@class="url_short_desc"]/text()')[0]
        except:
            desc = ''
        # 国旗
        try:
            flag = siteDiv.xpath('.//span[2]/@class')[0]
        except:
            flag = ''
        siteList.append({
            "title": title, # PornHub
            "orgin": orgin, # https://theporndude.com/zh/566/pornhub
            "desc": desc, # PornHub.com是世界上最大的免费色情分享网站之一，有超过110....
            "flag": flag
        })
    return siteList

# 抓取分类相关数据 传入html 或 element
def extractCategoryData(categoryElement):
    ## 判断是否为字符串
    if isinstance(categoryElement, str):
        categoryElement = etree.HTML(categoryElement)

    # 提取分类名称和描述
    categoryName = categoryElement.xpath('.//h2/a/text()')[0]
    categoryDesc = categoryElement.xpath('.//p[@class="desc"]/text()')[0]
    try:
        categoryShortDesc = categoryElement.xpath('./div[2]/div/text()')[0]
    except:
        categoryShortDesc = ''
    titleClass = categoryElement.xpath('.//h2/span/@class')[0]
    categoryIcon = extractCategoryIcon(titleClass.split(' ')[1])
    # 提取分类详情中的信息
    categoryUrl = categoryElement.xpath('.//h2/a/@href')[0]
    categoryDetailTree = etree.HTML(
        fetchData(categoryUrl)
    )
    categorySlogan = categoryDetailTree.xpath('/html/body/div[1]/div[2]/div/div[3]/h1/span[2]/text()')[0]
    categoryContent =etree.tostring(categoryDetailTree.xpath('.//div[contains(@class,"category-desc")]/.')[0],method='html', encoding='unicode')
    # 移除categoryContent最外层div
    categoryContent = categoryContent[
        len('<div class="category-desc-wrapper v-scroll bottom-shadow"><div class="category-desc scrollbox">'):
        -len('</div></div>')
    ]
    categoryThumb = ""
    # 获取分类Thumb
    for item in categoryDetailTree.xpath('//*[@class="url_links_wrapper url_links_wrapper_related"]//a'):
        if item.xpath('.//span/text()')[0] == categoryName:
            categoryThumb = item.xpath('.//img/@data-src')[0]
            break

    # # 包含data-visit-category-id的a标签
    # categoryUrl = categoryElement.xpath('//*[@data-visit-category-id]/@href')[0]
    # 提取链接数据项
    dataItems = extractSiteListByCategoryUrl(categoryUrl)
    # 首页中展示的站点数量
    homeCount = len(categoryElement.xpath('.//ul/li'))

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
                        'ratingCount': detail['ratingCount'],
                        'thumbImg': detail['thumbImg'],
                        'prosComment': detail['prosComment'],
                        'consComment': detail['consComment'],
                        'content': detail['content'],
                    })
                    temp_dict[item['title']] = item
                    print(f"抓取数据成功： {item['title']}  {item['url']}")
                    break
                except Exception as exc:
                    print(f"抓取详情失败: {exc} 尝试次数：{attempt}  {item['title']}  {item['orgin']}  错误信息: {exc}")
                    time.sleep(1)

    # 保证最终数据的顺序一致性
    linkList = [temp_dict[item['title']] for item in dataItems if item['title'] in temp_dict]
    return {
        "categoryName": categoryName,  # 免费色情视频网站
        "categoryDesc": categoryDesc,  # 在世界上最流行的色情视频网站上观看免费的高清色情视频....
        "categoryShortDesc": categoryShortDesc, # 在XXX世界中最流行的色情视频网站上观看免费的色情视频。
        "categoryIcon": categoryIcon, # https://media.porndudecdn.com/includes/images/categories/FREE-PORN-TUBE-SITES.svg
        "categoryThumb" : categoryThumb, # https://assets.tpdfiles.com/includes/images/cthumbnails/43_30b29_thumb.png
        "categorySlogan": categorySlogan, # 免费色情视频网站
        "categoryContent": categoryContent, #<div>xxxx</div>
        "homeCount": homeCount, # 首页展示的数量
        "allCount": len(linkList), # 当前分类所有站点数量
        "linkList": linkList,
    }

def getData(baseUrl):
    # 存盘路径
    savePath = "./datas/" + baseUrl[-2:]
    # 创建文件夹
    if not os.path.exists(savePath):
        os.makedirs(savePath)
    # baseUrl = "https://theporndude.com/zh"
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
        with open(f"{savePath}/outPornDude-{storgePage}.json", "w", encoding="utf-8") as f:
            f.write(jsonStr)
        print("=========数据存盘===========：" + f"{savePath}/outPornDude-{storgePage}.json")
        storgePage += 1

    # 加载更多异步数据
    pattern = r'https://assets.tpdfiles.com/includes/pi/.+.passive.info.js'
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
                        with open(f"{savePath}/outPornDude-{storgePage}.json", "w", encoding="utf-8") as f:
                            f.write(jsonStr)
                        print("=========数据存盘===========" + f"{savePath}/outPornDude-{storgePage}.json")
                        storgePage += 1
        else:
            print("请求js文件失败：" + match.group())

if __name__ == '__main__':
    langUrl = [
        # "https://theporndude.com/en",
        # "https://theporndude.com/ar",
        # "https://theporndude.com/cs",
        # "https://theporndude.com/da",
        # "https://theporndude.com/de",
        # "https://theporndude.com/el",
        # "https://theporndude.com/es",
        # "https://theporndude.com/fi",
        # "https://theporndude.com/fr",
        # "https://theporndude.com/he",
        # "https://theporndude.com/hi",
        # "https://theporndude.com/hr",
        # "https://theporndude.com/hu",
        # "https://theporndude.com/id",
        # "https://theporndude.com/it",
        # "https://theporndude.com/ja",
        # "https://theporndude.com/ko",
        # "https://theporndude.com/nl",
        # "https://theporndude.com/no",
        # "https://theporndude.com/pl",
        # "https://theporndude.com/pt",
        # "https://theporndude.com/ro",
        # "https://theporndude.com/ru",
        # "https://theporndude.com/sl",
        "https://theporndude.com/sv",
        "https://theporndude.com/th",
        "https://theporndude.com/tr",
        "https://theporndude.com/vi",
        # "https://theporndude.com/zh",
    ]
    # for item in langUrl:
    #     getData(item)
    #     time.sleep(60)


    #
    #
    #
    # sed -i 's|getData("https://theporndude.com/[^"]*")|getData("https://theporndude.com/ar")|g' spider_theporndude.py &&
    print("开始执行采集任务...")
    # getData("https://theporndude.com/pt")
    # getData("https://theporndude.com/ro")
    # getData("https://theporndude.com/ru")
    getData("https://theporndude.com/sl")
    getData("https://theporndude.com/sv")
    getData("https://theporndude.com/th")
    # getData("https://theporndude.com/tr")
    # getData("https://theporndude.com/vi")
    # print("获取分类数量：" + str(len(r)))
    # print("获取链接数量：" + str(sum([len(item["linkList"]) for item in r])))
    # jsonStr = json.dumps(r, ensure_ascii=False, indent=4)
    # print(jsonStr)
    # # 写入本地文件  out.json
    # with open("../datas/outPornDude.json", "w", encoding="utf-8") as f:
    #     f.write(jsonStr)
