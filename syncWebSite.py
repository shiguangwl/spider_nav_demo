from collections import defaultdict

from common.Logger import logger
from spider.spider_admin import getCategoty, init, addCategory, getLinkDescAll, addLink, updateLinkInfo
from spider.spider_site import spiderSite

if __name__ == '__main__':
    spderData = spiderSite()

    # # TEST data
    # spderData = []
    # with open('outSite.json', 'r') as file:
    #     spderData = json.load(file)
    # mySesion = init()

    init()
    # 开始同步父父类
    logger.info("开始同步分类")
    logger.info("开始获取本地分类")
    currentCategoryList = getCategoty()
    spiderParentNameSet = {items['parentName'] for items in spderData}
    currentParentNameSet = set()
    currentChildNameSet = set()
    for item in currentCategoryList:
        if item['parent']['id'] == '' or item['parent']['id'] == '-1':
            currentParentNameSet.add(item['title'])
        else:
            currentChildNameSet.add(item['title'])
    addParentNameSet = spiderParentNameSet - currentParentNameSet
    logger.info(f"需要添加的父分类：{addParentNameSet}")
    if len(addParentNameSet) > 0:
        for item in addParentNameSet:
            logger.info(f"开始添加父分类：{item}")
            # 查找目标父分类数据
            addCategory(
                categoryName=item,
                categorySlug=item,
                categoryParent='-1',
                categoryDescription=item,
                categorySeoTitle=item,
                categorySeoMetakey=item,
                categorySeoDesc=item,
            )
    else:
        logger.info("本地一级分类无变更数据")

    # 同步子分类
    logger.info("开始同步二级分类")
    logger.info("开始获取本地分类数据")
    currentCategoryList = getCategoty()
    # 根据spderData的parentName进行分组
    spiderParentNameDict = defaultdict(list)
    for item in spderData:
        spiderParentNameDict[item['parentName']].append(item)
    # 遍历spiderParentNameDict
    for key, value in spiderParentNameDict.items():
        # 查找父分类ID
        parentId = -1
        for item in currentCategoryList:
            if (item['parent']['id'] == '' or item['parent']['id'] == '-1') and item['title'] == key:
                parentId = item['id']
                break
        for item in value:
            # 判断子分类是否存在不存在则添加
            if item['childCategoryName'] in currentChildNameSet:
                logger.info(f"子分类： {item['childCategoryName']} 已经存在 父分类ID : {parentId}")
                continue
            logger.info(f"开始添加子分类：{item['childCategoryName']} 父分类ID : {parentId}")
            addCategory(
                categoryName=item['childCategoryName'],
                categorySlug=item['childCategoryName'],
                categoryParent=str(parentId),
                categoryDescription=item['childCategoryName'],
                categorySeoTitle=item['childCategoryName'],
                categorySeoMetakey=item['childCategoryName'],
                categorySeoDesc=item['childCategoryName'],
            )

    # 开始插入链接数据
    logger.info("准备开始同步站点数据")
    logger.info("获取本地分类数据")
    currentCategoryList = getCategoty()
    logger.info("获取本地链接数据")
    currentLinkDatas = getLinkDescAll()
    for item in spderData:
        parentCategoryName = item['parentName']
        childCategoryName = item['childCategoryName']
        logger.info(f"开始同步分类：{parentCategoryName} 子分类：{childCategoryName}")
        for childItem in item['linkList']:
            # 查找对应的分类ID
            cId = -1
            for e in currentCategoryList:
                if e['title'] == childCategoryName and e['parent']['title'] == parentCategoryName:
                    cId = e['id']
                    break
            # 判断是否已经存在当前链接数据
            currentLink = None
            for currentLinkData in currentLinkDatas:
                cName = ''
                for e in currentCategoryList:
                    if e['id'] == currentLinkData['categoryId']:
                        cName = e['title']
                        break
                if currentLinkData['title'] == childItem['title'] and cName == childCategoryName:
                    logger.info(f"{childItem['title']} {childItem['detail']['siteLink']} 已经存在")
                    currentLink = currentLinkData
                    break

            if currentLink is None:
                logger.info(f"开始添加链接：{childItem['title']} {childItem['detail']['siteLink']} 所属分类：{parentCategoryName} - {childCategoryName} 分类ID：{cId}")
                # 新增
                # 去除正文广告
                content = childItem['detail']['content']
                content = content[:content.rfind('<hr/>')]
                # content = content.replace('https://007tg.com', '#TEMP#')
                # 查找最后一个 <hr/> 截取之前内容，判断是否包含 ‘联系我们’ 或 ‘007TG’ 如果包含基本为广告，在正文中剔除数据
                # lastHtml = content[content.rfind('<hr>'):]
                if '联系我们' in content or '007TG' in content:
                    content = content[:content.rfind('<hr/>')]
                content = content.replace('007TG', '柒彩出海导航')
                # 恢复链接 不影响图片显示
                # content = content.replace('#TEMP#','https://007tg.com')
                addLink(
                    title=childItem['title'],
                    content=content,
                    siteLink=childItem['detail']['siteLink'],
                    categoryId=cId,
                    desc=childItem['detail']['desc'],
                    tags='',
                    seo_title=childItem['title'],
                    seo_metake=childItem['detail']['seo_keywords'],
                    seo_desc=childItem['detail']['seo_description'],
                )
            else:
                # 判断是否需要更新数据
                if currentLink['siteLink'] != childItem['detail']['siteLink']:
                    logger.info(f"{childItem['title']} {childItem['detail']['siteLink']} 所属分类：{parentCategoryName} - {childCategoryName} 分类ID：{cId} 数据需要更新")
                    updateLinkInfo(
                        postId=currentLink['id'],
                        title=childItem['title'],
                        content=childItem['detail']['content'],
                        siteLink=childItem['detail']['siteLink'],
                        categoryId=cId,
                        desc=childItem['detail']['desc'],
                        tags='',
                        seo_title=childItem['title'],
                        seo_metakey=childItem['detail']['seo_keywords'],
                        seo_desc=childItem['detail']['seo_description'],
                    )
                else:
                    logger.info(f"{childItem['title']} {childItem['detail']['siteLink']} 所属分类：{parentCategoryName} - {childCategoryName} 分类ID：{cId} 数据无需更新")


