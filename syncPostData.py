# 同步博文数据
import json
import time

from Logger import logger
from spider_admin import postBlog, getPost
from spider_site import getBlogDatas

if __name__ == '__main__':
    channels = [
        'https://007tg.com/007-channel',
        'https://007tg.com/about-us/007live',
        'https://007tg.com/about-us/zhanglaotalking',
    ]

    blogDatas = getBlogDatas(channels)
    jsonStr = json.dumps(blogDatas)
    # 写入本地文件
    with open("outBlog.json", "w", encoding="utf-8") as f:
        f.write(jsonStr)

    # # 加载本地json数据
    # blogDatas = []
    # with open('outBlog.json', 'r') as file:
    #     blogDatas = json.load(file)

    logger.info(f"博文数据总数：{len(blogDatas)}")
    blogDatas.reverse()
    logger.info("准备开始同步博文数据")
    allPostData = getPost()
    for blogData in blogDatas:
        if blogData['title'].replace('007TG', '').replace('007出海','柒彩出海') not in allPostData:
            logger.info(f"{blogData['title']} 开始同步")
            try:
                postBlog(blogData)
            except Exception as e:
                logger.error(f"{blogData['title']} 同步失败 e：{e}")
                time.sleep(3)
        else:
            logger.info(f"{blogData['title']} 已存在")
