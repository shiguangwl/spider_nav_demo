import math
import time

import requests
from lxml import etree
import json

from Logger import logger


def spiderSite():
    """
    [
        {
            "parentName": "跨境服务",
            "childCategoryName": "广告代理",
            "childCategoryLink": "https://007tg.com/favorites/advertising-agency/",
            "linkList": [
                {
                    "title": "飞书互动",
                    "link": "https://007tg.com/sites/1550.html",
                    "detail": {
                        "title": "飞书互动-007TG全球社交流量导航",
                        "content": "<p>正文</p> ",
                        "siteLink": "https://www.meetsocial.cn/",
                        "desc": "Facebook官方授权代理商",
                        "seo_keywords": "飞书互动,007TG全球社交流量导航",
                        "seo_description": "Facebook官方授权代理商"
                    }
                },
            ]
        }
    ]
    :return:
    """
    rData = []
    siteText = requests.get("https://007tg.com/").text
    htmlTree = etree.HTML(siteText)
    contentEl = htmlTree.xpath('//*[@class="content-layout"]')[0]
    # 父分类
    parentEls = contentEl.xpath("./h4")
    for parentEl in parentEls:
        parentName = parentEl.xpath('string(.)').strip()
        tabsEl = parentEl.getnext().getnext()
        chilCategoryNames = tabsEl.xpath('.//ul/li//a')
        categotyLink = tabsEl.xpath('.//ul/li//a/@data-link')
        termIds = tabsEl.xpath('.//ul/li//a/@id')
        # logger.warning(categotyLink)
        # logger.warning(termIds)
        for i in range(len(chilCategoryNames)):
            childCategoryName = chilCategoryNames[i].xpath('string(.)')
            childCategoryLink = categotyLink[i]
            cItem = {
                "parentName": parentName,
                "childCategoryName": childCategoryName,
                "childCategoryLink": childCategoryLink
            }
            logger.info("开始采集 ：" + parentName + " - " + childCategoryName)

            url = "https://007tg.com/wp-admin/admin-ajax.php"
            params = {
                "id": termIds[i].split("-")[1],
                "taxonomy": "favorites",
                "action": "load_home_tab",
                "post_id": 0
            }
            response = requests.get(url, params=params).text
            tabsHtmlTree = etree.HTML(response)
            linkList = []
            allLink = tabsHtmlTree.xpath('.//a')
            for item in allLink:
                link = {
                    "title": item.xpath('string(.//strong)'),
                    "link": item.xpath('./@href')[0],
                }
                try:
                    link["detail"] = spiderSiteDetail(link)
                    linkList.append(link)
                except Exception as e:
                    logger.warning(f"采集详情： {link['title']}     {link['link']}   采集失败")

            cItem['linkList'] = linkList
            # logger.info("采集 父类： " + parentName + " 子类：" + childCategoryName + "   " + json.dumps(cItem))
            rData.append(
                cItem
            )
    jsonStr = json.dumps(rData)
    # print(jsonStr)
    # 写入本地文件  out.json
    with open("outSite.json", "w", encoding="utf-8") as f:
        f.write(jsonStr)

    return rData

# 详情数据
def spiderSiteDetail(linkDict):
    link = linkDict['link']
    logger.info(f"采集详情： {linkDict['title']}     {link}")
    htmlText = requests.get(link).text
    htmlTree = etree.HTML(htmlText)

    title = htmlTree.xpath('string(//title)')
    content = str(etree.tostring(htmlTree.xpath('//*[@id="content"]/main/div[1]/div/div[1]/div/div[2]')[0]))[2:-1]
    siteLink = htmlTree.xpath('//*[@id="content"]/div/div[3]/div/div/div/span/a/@href')[0]
    desc = htmlTree.xpath('string(//*[@id="content"]/div/div[3]/div/div/p[1])').replace('007TG', '柒彩出海导航')
    seo_keywords = htmlTree.xpath('string(//meta[@name="keywords"]/@content)').replace('007TG', '柒彩出海导航')
    seo_description = htmlTree.xpath('string(//meta[@name="description"]/@content)').replace('007TG', '柒彩出海导航')

    return {
        "title": title,
        "content": content.replace(r'\n',''),
        "siteLink": siteLink,
        "desc": desc,
        "seo_keywords": seo_keywords,
        "seo_description": seo_description
    }



def getBlogDatas(categoryUrlList):
    rData = []
    for categoryUrl in categoryUrlList:
        pageNum = 1
        currentPageNum = 1
        logger.info("开始采集分类 ：" + categoryUrl)
        while pageNum == -1 or currentPageNum <= pageNum:
            url = categoryUrl + '/page/' + str(currentPageNum)
            logger.info(f"采集分类 ：{url}  第 {currentPageNum} 页")
            htmlText = requests.get(url).text
            htmlTree = etree.HTML(htmlText)
            pageNum = int(htmlTree.xpath('//*[@class="posts-nav"]/*/text()')[-1])
            categoryTitle = htmlTree.xpath("string(//*[@id='content']/div[1]/div/div[1]/h1)").replace(f'\r\n','').strip()
            categoryDesc = htmlTree.xpath('string(//*[@id="content"]/div[1]/div/div[1]/p)').strip()
            for item in htmlTree.xpath('//*[@id="content"]/div[1]/div/div[2]/div'):
                title = item.xpath('.//h2/a/@title')[0]
                link = item.xpath('.//h2/a/@href')[0]
                # 摘要
                desc = item.xpath('string(./div/div[2]/div[1]/div/div)').strip()
                # 获取详情信息
                logger.info(f"开始采集详情： {title}     {link}")
                detail = spiderBlogDetail(link)
                rData.append({
                    "categoryTitle": categoryTitle,
                    "categoryDesc": categoryDesc,
                    "title": title,
                    "desc": desc,
                    "link": link,
                    "content" : detail['content'],
                    "tags": detail['tags'],
                })
            currentPageNum += 1
    return rData



def spiderBlogDetail(link):
    htmlTree = etree.HTML(requests.get(link).text)
    title = htmlTree.xpath('//*[@id="content"]/main/div[1]/div/div[1]/div/div[1]/h1/text()')[0]
    content = str(etree.tostring(htmlTree.xpath('//*[@id="content"]/main/div[1]/div/div[1]/div/div[3]')[0])).replace(r'\n','')[2:-1]
    tags = htmlTree.xpath('//*[@id="content"]/main/div[1]/div/div[1]/div/div[4]/a/text()')
    return {
        "title": title,
        "content": content,
        "tags": tags
    }




if __name__ == '__main__':
    pass
    # 计算耗时
    start = time.time()
    spiderSite()
    end = time.time()
    logger.info("耗时：" + str(end - start))

    # 计算耗时
    # start = time.time()
    # channels = [
    #     'https://007tg.com/007-channel/',
    #     'https://007tg.com/about-us/007live/',
    #     'https://007tg.com/about-us/zhanglaotalking/',
    # ]
    #
    # dats = getBlogDatas(channels)
    # jsonStr = json.dumps(dats)
    # # print(jsonStr)
    # # 写入本地文件  out.json
    # with open("outBlog.json", "w", encoding="utf-8") as f:
    #     f.write(jsonStr)
    # end = time.time()
    # logger.info("耗时：" + str(end - start))




