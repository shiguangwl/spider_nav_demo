import math
import random
import re
import uuid
from urllib.parse import quote

from pypinyin import pinyin, Style
from wordpress_xmlrpc import WordPressPost, Client
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost
import requests
from lxml import etree
import json
import html


from common.Logger import logger

mySession = requests.session()
domain = ""

# 获取分类数据
# [
# {
#     "id": "49",
#     "title": "我是标题",
#     "slug": "我是别名",
#     "parent": {
#         "id": "25",
#         "title": "网址分类222"
#     },
#     "desc": "我是描述",
#     "customTitle": "自定义标题",
#     "keyword": "关键词",
#     "customDesc": "自定义描述"
# }
# ]
def getCategoty():
    rdata = []
    pageNum = 1
    cureentPage = 1

    while (cureentPage <= pageNum):
        url = f"{domain}/wp-admin/edit-tags.php?taxonomy=favorites&post_type=sites&paged=" + str(cureentPage)
        html_str = mySession.get(
            url,
        ).text
        html = etree.HTML(html_str)
        # 获取最大页数
        pageNum = html.xpath('string(//*[@id="posts-filter"]/div[2]/div[2]/span[1])')
        if (pageNum.find('项') != -1):
            pageNum = math.ceil(int(pageNum.split(' ')[0]) / 20)
        else:
            pageNum = 1

        trs = html.xpath("//*[@id='the-list']//*[contains(@id, 'tag-')]")
        # 便利trs 输出html
        for tr in trs:
            descLink = tr.xpath('.//strong/a/@href')[0]
            # 请求获取详情信息
            descHtml = mySession.get(descLink).text
            descHtml = etree.HTML(descHtml)
            # 分类id
            id = descHtml.xpath('//*[@id="edittag"]/input[2]/@value')[0]
            # 名称
            title = descHtml.xpath('//*[@id="name"]/@value')[0]
            # 别名
            slug = descHtml.xpath('//*[@id="slug"]/@value')[0]
            # 父类名 / 父类id
            parent = {
                "id": '',
                "title": '',
            }
            select = descHtml.xpath('//*[@id="parent"]')[0]
            selectItem = select.xpath('./option[@selected="selected"]')
            # 是否有选中分类
            if len(selectItem) > 0:
                parent["id"] = selectItem[0].xpath('./@value')[0]
                parent["title"] = selectItem[0].xpath('./text()')[0]
            # 描述
            desc = descHtml.xpath('string(//*[@id="description"])')
            # 自定义标题
            customTitle = descHtml.xpath('//*[@id="edittag"]/div[1]/div[4]/div[2]/input/@value')[0]
            # 关键词
            keyword = descHtml.xpath('//*[@id="edittag"]/div[1]/div[5]/div[2]/input/@value')[0]
            # 自定义描述
            customDesc = descHtml.xpath('string(//*[@id="edittag"]/div[1]/div[6]/div[2]/textarea)')
            rdata.append({
                "id": id,
                "title": title,
                "slug": slug,
                "parent": parent,
                "desc": desc,
                "customTitle": customTitle,
                "keyword": keyword,
                "customDesc": customDesc,
            })
        cureentPage += 1
    return rdata


# 获取所有网址数据
# {
#     "id": "1",
#     "title": "测试标题sdf sdf dsf sd dsf",
#     "content": "我是测试内容\r\n\r\n \r\n\r\n \r\n\r\n<strong>书法的身份都是</strong>",
#     "siteLink": "http://baidu.com",
#     "categoryId": "37",
#     "categoryName": "我是分类",
#     "desc": "一句话描述"
# }
def getLinkDescAll():
    rdata = []
    pageNum = 1
    currentPage = 1
    while (currentPage <= pageNum):
        url = f"{domain}/wp-admin/edit.php?post_type=sites&paged=" + str(currentPage)
        html_text = mySession.get(url).text
        html_tree = etree.HTML(html_text)
        # 获取总页数
        pageNum = int(html_tree.xpath('string(//*[@id="table-paging"]/span/span)'))
        # 获取当前页数据
        trs = html_tree.xpath('//*[@id="the-list"]//tr')
        for tr in trs:
            descLink = tr.xpath('.//strong/a/@href')
            if len(descLink) > 0:
                descLink = descLink[0]
            else:
                continue
            logger.info("开始抓取后台数据： " + descLink)
            # descLink = 'https://c7c.com/wp-admin/post.php?post=924&action=edit'
            desc_text = mySession.get(descLink).text
            html_tree = etree.HTML(desc_text)
            # id  https://c7c.com/sites/1157.html 截取  1157
            id = html_tree.xpath('//*[@id="sample-permalink"]/@href')[0].split('/')[-1].split('.')[0]
            # 标题
            title = html_tree.xpath('//*[@id="title"]/@value')[0]
            # 正文内容 html
            content = html.unescape(html_tree.xpath('string(//textarea[@id="content"])'))
            # 站点链接
            siteLink = \
                html_tree.xpath(
                    '//*[@id="sites_post_meta"]/div[2]/div/div/div[2]/div/div[1]/div[7]/div[2]/input/@value')[0]
            # 站点分类id
            categoryId_values = html_tree.xpath(
                '//*[@id="favoriteschecklist"]//li/label/input[@checked="checked"]/@value')
            categoryId = categoryId_values[0] if categoryId_values else ""
            # # 站点分类名称
            # categoryName = html_tree.xpath('string(//*[@id="favoriteschecklist"]//li[contains(@checked, "checked")]/label)')[1:]
            # 一句话描述
            desc = html_tree.xpath(
                'string(//*[@id="sites_post_meta"]/div[2]/div/div/div[2]/div/div[1]/div[9]/div[2]/textarea)')
            rdata.append({
                "id": id,
                "title": title,
                "content": content,
                "siteLink": siteLink,
                "categoryId": categoryId,
                # "categoryName": categoryName,
                "desc": desc,
            })
        currentPage += 1
    return rdata


# 获取指定分类id下的网址数据
def getLinkDesc(cid):
    allData = getLinkDescAll()
    return list(filter(lambda x: x["categoryId"] == str(cid), allData))


# 发布链接
def addLink(
        title: str,
        content: str,
        siteLink: str,
        categoryId: str,
        desc: str,
        tags: str,
        seo_title: str,
        seo_metake: str,
        seo_desc: str,
):
    # 获取表单校验参数
    newPageText = mySession.get(
        f"{domain}/wp-admin/post-new.php?post_type=sites"
    ).text

    newPageTree = etree.HTML(newPageText)
    _wpnonce = newPageTree.xpath('//input[@id="_wpnonce"]/@value')[0]
    post_ID = newPageTree.xpath('//input[@id="post_ID"]/@value')[0]
    meta_box_order_nonce = newPageTree.xpath('//input[@id="meta-box-order-nonce"]/@value')[0]
    closedpostboxesnonce = newPageTree.xpath('//input[@id="closedpostboxesnonce"]/@value')[0]
    samplepermalinknonce = newPageTree.xpath('//input[@id="samplepermalinknonce"]/@value')[0]
    csf_metabox_noncepage_option_post_meta = \
        newPageTree.xpath('//input[@id="csf_metabox_noncepage-option_post_meta"]/@value')[0]
    _ajax_nonce_add_favorites = newPageTree.xpath('//input[@id="_ajax_nonce-add-favorites"]/@value')[0]
    csf_metabox_noncepost_seo_post_meta = \
        newPageTree.xpath('//input[@id="csf_metabox_noncepost-seo_post_meta"]/@value')[0]
    csf_metabox_noncepage_parameter_post_meta = \
        newPageTree.xpath('//input[@id="csf_metabox_noncepage-parameter_post_meta"]/@value')[0]
    _ajax_nonce_add_meta = newPageTree.xpath('//input[@id="_ajax_nonce-add-meta"]/@value')[0]
    csf_metabox_noncesites_post_meta = newPageTree.xpath('//input[@id="csf_metabox_noncesites_post_meta"]/@value')[0]

    url = f"{domain}/wp-admin/post.php"
    payload = {
        "_wpnonce": _wpnonce,
        "_wp_http_referer": "/wp-admin/post-new.php?post_type=sites",
        "user_ID": "1",
        "action": "editpost",
        "originalaction": "editpost",
        "post_author": "1",
        "post_type": "sites",
        "original_post_status": "auto-draft",
        "post_ID": post_ID,
        "meta-box-order-nonce": meta_box_order_nonce,
        "closedpostboxesnonce": closedpostboxesnonce,
        "post_title": title,
        "samplepermalinknonce": samplepermalinknonce,
        "content": content,
        "csf_metabox_noncepage-option_post_meta": csf_metabox_noncepage_option_post_meta,
        "page-option_post_meta[sidebar_layout]": "default",
        "wp-preview": "",
        "hidden_post_status": "draft",
        "post_status": "draft",
        "hidden_post_password": "",
        "hidden_post_visibility": "public",
        "visibility": "public",
        "post_password": "",
        "original_publish": "发布",
        "publish": "发布",
        "tax_input[favorites][]": ["0", categoryId],
        "newfavorites": "New Genre Name",
        "_ajax_nonce-add-favorites": _ajax_nonce_add_favorites,
        "tax_input[sitetag]": tags,
        "newtag[sitetag]": "",
        "csf_metabox_noncepost-seo_post_meta": csf_metabox_noncepost_seo_post_meta,
        "post-seo_post_meta[_seo_title]": seo_title,
        "post-seo_post_meta[_seo_metakey]": seo_metake,
        "post-seo_post_meta[_seo_desc]": seo_desc,
        "csf_metabox_noncepage-parameter_post_meta": csf_metabox_noncepage_parameter_post_meta,
        "page-parameter_post_meta[views]": "0",
        "page-parameter_post_meta[_like_count]": "0",
        "page-parameter_post_meta[_down_count]": "0",
        "meta[1333][key]": "views",
        "meta[1333][value]": "0",
        "metakeyselect": "#NONE#",
        "metakeyinput": "",
        "metavalue": "",
        "_ajax_nonce-add-meta": _ajax_nonce_add_meta,
        "advanced_view": "1",
        "comment_status": "close",
        "post_name": "",
        "post_author_override": "1",
        "csf_metabox_noncesites_post_meta": csf_metabox_noncesites_post_meta,
        "sites_post_meta[_sites_type]": "sites",
        "sites_post_meta[_goto]": "",
        "sites_post_meta[_wechat_id]": "",
        "sites_post_meta[_is_min_app]": "",
        "sites_post_meta[_sites_link]": siteLink,
        "___sites_post_meta[_spare_sites_link][0][spare_name]": "",
        "___sites_post_meta[_spare_sites_link][0][spare_url]": "",
        "___sites_post_meta[_spare_sites_link][0][spare_note]": "",
        "sites_post_meta[_sites_sescribe]": desc,
        "sites_post_meta[_sites_language]": "",
        "sites_post_meta[_sites_country]": "",
        "sites_post_meta[_sites_order]": "0",
        "sites_post_meta[_thumbnail]": "",
        "sites_post_meta[_sites_preview]": "",
        "sites_post_meta[_wechat_qr]": "",
        "sites_post_meta[_down_version]": "",
        "sites_post_meta[_down_size]": "",
        "___sites_post_meta[_down_url_list][0][down_btn_name]": "百度网盘",
        "___sites_post_meta[_down_url_list][0][down_btn_url]": "",
        "___sites_post_meta[_down_url_list][0][down_btn_tqm]": "",
        "___sites_post_meta[_down_url_list][0][down_btn_info]": "",
        "sites_post_meta[_dec_password]": "",
        "sites_post_meta[_down_preview]": "",
        "sites_post_meta[_down_formal]": "",
        "___sites_post_meta[_screenshot][0][img]": "",
        "sites_post_meta[_user_purview_level]": "all",
        "sites_post_meta[buy_option][buy_type]": "view",
        "sites_post_meta[buy_option][limit]": "all",
        "sites_post_meta[buy_option][pay_type]": "money",
        "sites_post_meta[buy_option][price_type]": "single",
        "sites_post_meta[buy_option][pay_title]": "",
        "sites_post_meta[buy_option][pay_price]": "0",
        "sites_post_meta[buy_option][price]": "0",
        "___sites_post_meta[buy_option][annex_list][0][index]": "1",
        "___sites_post_meta[buy_option][annex_list][0][link]": "",
        "___sites_post_meta[buy_option][annex_list][0][name]": "",
        "___sites_post_meta[buy_option][annex_list][0][pay_price]": "0",
        "___sites_post_meta[buy_option][annex_list][0][price]": "0",
        "___sites_post_meta[buy_option][annex_list][0][info]": ""
    }

    mySession.post(url, data=payload)

    logger.info(f"链接已提交：https://c7c.com/sites/{post_ID}.html")


# 修改链接
def updateLinkInfo(
        postId: str,
        title: str,
        content: str,
        siteLink: str,
        categoryId: str,
        desc: str,
        tags: str,
        seo_title: str,
        seo_metakey: str,
        seo_desc: str,
):
    # 获取表单校验参数
    newPageText = mySession.get(
        f"{domain}/wp-admin/post.php?post={postId}&action=edit"
    ).text

    newPageTree = etree.HTML(newPageText)
    _wpnonce = newPageTree.xpath('//input[@id="_wpnonce"]/@value')[0]
    meta_box_order_nonce = newPageTree.xpath('//input[@id="meta-box-order-nonce"]/@value')[0]
    closedpostboxesnonce = newPageTree.xpath('//input[@id="closedpostboxesnonce"]/@value')[0]
    samplepermalinknonce = newPageTree.xpath('//input[@id="samplepermalinknonce"]/@value')[0]
    _ajax_nonce_add_favorites = newPageTree.xpath('//input[@id="_ajax_nonce-add-favorites"]/@value')[0]
    csf_metabox_noncepost_seo_post_meta = \
        newPageTree.xpath('//input[@id="csf_metabox_noncepost-seo_post_meta"]/@value')[0]
    csf_metabox_noncepage_parameter_post_meta = \
        newPageTree.xpath('//input[@id="csf_metabox_noncepage-parameter_post_meta"]/@value')[0]
    _ajax_nonce_add_meta = newPageTree.xpath('//input[@id="_ajax_nonce-add-meta"]/@value')[0]
    csf_metabox_noncesites_post_meta = newPageTree.xpath('//input[@id="csf_metabox_noncesites_post_meta"]/@value')[0]

    add_comment_nonce = newPageTree.xpath('//input[@id="add_comment_nonce"]/@value')[0]
    _ajax_fetch_list_nonce = newPageTree.xpath('//input[@id="_ajax_fetch_list_nonce"]/@value')[0]

    url = 'https://c7c.com/wp-admin/post.php'

    data = {
        '_wpnonce': _wpnonce,
        '_wp_http_referer': f'/wp-admin/post.php?post={postId}&action=edit',
        'user_ID': '1',
        'action': 'editpost',
        'originalaction': 'editpost',
        'post_author': '1',
        'post_type': 'sites',
        'original_post_status': 'publish',
        'referredby': 'https://c7c.com/wp-admin/edit.php?post_type=sites',
        '_wp_original_http_referer': 'https://c7c.com/wp-admin/edit.php?post_type=sites',
        'post_ID': postId,
        'meta-box-order-nonce': meta_box_order_nonce,
        'closedpostboxesnonce': closedpostboxesnonce,
        'post_title': title,
        'samplepermalinknonce': samplepermalinknonce,
        'content': content,
        'csf_metabox_nonce': csf_metabox_noncesites_post_meta,
        'page-option_post_meta[sidebar_layout]': 'default',
        'wp-preview': '',
        'hidden_post_status': 'publish',
        'post_status': 'publish',
        'hidden_post_password': '',
        'hidden_post_visibility': 'public',
        'visibility': 'public',
        'post_password': '',
        'original_publish': '更新',
        'save': '更新',
        'tax_input[favorites][]': ['0', categoryId],
        'newfavorites': 'New Genre Name',
        'newfavorites_parent': '-1',
        '_ajax_nonce-add-favorites': _ajax_nonce_add_favorites,
        'tax_input[sitetag]': tags,
        'newtag[sitetag]': '',
        'csf_metabox_noncepost-seo_post_meta': csf_metabox_noncepost_seo_post_meta,
        'post-seo_post_meta[_seo_title]': seo_title,
        'post-seo_post_meta[_seo_metakey]': seo_metakey,
        'post-seo_post_meta[_seo_desc]': seo_desc,
        'csf_metabox_noncepage-parameter_post_meta': csf_metabox_noncepage_parameter_post_meta,
        'page-parameter_post_meta[views]': '1',
        'page-parameter_post_meta[_like_count]': '0',
        'page-parameter_post_meta[_down_count]': '0',
        'meta[1725][key]': 'sidebar_layout',
        'meta[1725][value]': 'default',
        'meta[1716][key]': 'views',
        'meta[1716][value]': '1',
        'metakeyselect': '#NONE#',
        'metakeyinput': '',
        'metavalue': '',
        '_ajax_nonce-add-meta': _ajax_nonce_add_meta,
        'advanced_view': '1',
        "comment_status": "close",
        'add_comment_nonce': add_comment_nonce,
        '_ajax_fetch_list_nonce': _ajax_fetch_list_nonce,
        # 'post_name': '测试添加文章-post-2',
        'post_author_override': '1',
        'csf_metabox_noncesites_post_meta': csf_metabox_noncesites_post_meta,
        'sites_post_meta[_sites_type]': 'sites',
        'sites_post_meta[_goto]': '',
        'sites_post_meta[_wechat_id]': '',
        'sites_post_meta[_is_min_app]': '',
        'sites_post_meta[_sites_link]': siteLink,
        '___sites_post_meta[_spare_sites_link][0][spare_name]': '',
        '___sites_post_meta[_spare_sites_link][0][spare_url]': '',
        '___sites_post_meta[_spare_sites_link][0][spare_note]': '',
        'sites_post_meta[_sites_sescribe]': desc,
        'sites_post_meta[_sites_language]': '',
        'sites_post_meta[_sites_country]': '',
        'sites_post_meta[_sites_order]': '0',
        'sites_post_meta[_thumbnail]': '',
        'sites_post_meta[_sites_preview]': '',
        'sites_post_meta[_wechat_qr]': '',
        'sites_post_meta[_down_version]': '',
        'sites_post_meta[_down_size]': '',
        '___sites_post_meta[_down_url_list][0][down_btn_name]': '百度网盘',
        '___sites_post_meta[_down_url_list][0][down_btn_url]': '',
        '___sites_post_meta[_down_url_list][0][down_btn_tqm]': '',
        '___sites_post_meta[_down_url_list][0][down_btn_info]': '',
        'sites_post_meta[_dec_password]': '',
        'sites_post_meta[_down_preview]': '',
        'sites_post_meta[_down_formal]': '',
        '___sites_post_meta[_screenshot][0][img]': '',
        'sites_post_meta[_user_purview_level]': 'all',
        'sites_post_meta[buy_option][buy_type]': 'view',
        'sites_post_meta[buy_option][limit]': 'all',
        'sites_post_meta[buy_option][pay_type]': 'money',
        'sites_post_meta[buy_option][price_type]': 'single',
        'sites_post_meta[buy_option][pay_title]': '',
        'sites_post_meta[buy_option][pay_price]': '0',
        'sites_post_meta[buy_option][price]': '0',
        '___sites_post_meta[buy_option][annex_list][0][index]': '1',
        '___sites_post_meta[buy_option][annex_list][0][link]': '',
        '___sites_post_meta[buy_option][annex_list][0][name]': '',
        '___sites_post_meta[buy_option][annex_list][0][pay_price]': '0',
        '___sites_post_meta[buy_option][annex_list][0][price]': '0',
        '___sites_post_meta[buy_option][annex_list][0][info]': ''
    }

    response = mySession.post(url, data=data)
    logger.info(f"链接已更新：https://c7c.com/sites/{postId}.html")


def chinese_to_pinyin(text):
    # 将中文转换为拼音
    pinyin_list = pinyin(text, style=Style.NORMAL)
    return ''.join([item[0] for item in pinyin_list])


# 添加分类
def addCategory(
        categoryName: str,
        categorySlug: str,
        categoryParent: str,
        categoryDescription: str,
        categorySeoTitle: str,
        categorySeoMetakey: str,
        categorySeoDesc: str,
):
    categorySlug = chinese_to_pinyin(categorySlug)
    # 获取表单校验参数
    newPageText = mySession.get(
        f"{domain}/wp-admin/edit-tags.php?taxonomy=favorites&post_type=sites"
    ).text
    newPageTree = etree.HTML(newPageText)
    _wpnonce_add_tag = newPageTree.xpath("//input[@name='_wpnonce_add-tag']/@value")[0]
    # csf_taxonomy_noncefavorites_options = \
    # newPageTree.xpath("//input[@name='csf_taxonomy_noncefavorites_options']/@value")[0]

    url = 'https://c7c.com/wp-admin/admin-ajax.php'
    data = {
        'action': 'add-tag',
        'screen': 'edit-favorites',
        'taxonomy': 'favorites',
        'post_type': 'sites',
        '_wpnonce_add-tag': _wpnonce_add_tag,
        '_wp_http_referer': '/wp-admin/edit-tags.php?taxonomy=favorites&post_type=sites',
        'tag-name': categoryName,
        'slug': categorySlug,
        'parent': categoryParent,
        'description': categoryDescription,
        'csf_taxonomy_noncefavorites_options': csf_taxonomy_noncefavorites_options,
        '_wp_http_referer': '/wp-admin/edit-tags.php?taxonomy=favorites&post_type=sites',
        'favorites_options[_term_order]': '0',
        'favorites_options[seo_title]': categorySeoTitle,
        'favorites_options[seo_metakey]': categorySeoMetakey,
        'favorites_options[seo_desc]': categorySeoDesc,
        'favorites_options[card_mode]': 'null',
        'favorites_options[columns_type]': 'global',
        'favorites_options[columns][sm]': '2',
        'favorites_options[columns][md]': '2',
        'favorites_options[columns][lg]': '3',
        'favorites_options[columns][xl]': '5',
        'favorites_options[columns][xxl]': '6',
    }

    mySession.post(url, data=data)


def generate_random_number_string(length):
    # 生成一个随机整数
    random_number = random.randint(10 ** (length - 1), (10 ** length) - 1)
    # 将整数转换为字符串
    random_number_str = str(random_number)
    # 如果字符串长度小于预期长度，补零到指定长度
    while len(random_number_str) < length:
        random_number_str = '0' + random_number_str
    return random_number_str


# 同步主题左侧菜单
def syncMenu():
    logger.info("开始执行同步菜单")
    i = 0
    categoryList = getCategoty()
    pList = {}
    for categoryItem in categoryList:
        # 获取所有一级分类
        if categoryItem['parent']['id'] == '' or categoryItem['parent']['id'] == '-1':
            pList[f"nav_menu_item[-{categoryItem['id']}]"] = {
                "object_id": categoryItem['id'],
                "object": "favorites",
                "menu_item_parent": 0,
                "position": ++i,
                "type": "taxonomy",
                "title": categoryItem['title'],
                "url": f"{domain}/favorites/" + quote(categoryItem['title']),
                "target": "",
                "attr_title": "",
                "description": "",
                "classes": "",
                "xfn": "",
                "status": "publish",
                "original_title": categoryItem['title'],
                "nav_menu_term_id": 24,
                "_invalid": 'false',
                "type_label": "网址分类"
            }
        else:
            pList[f"nav_menu_item[-{categoryItem['id']}]"] = {
                "object_id": categoryItem['id'],
                "object": "favorites",
                "menu_item_parent": '-' + categoryItem['parent']['id'],
                "position": ++i,
                "type": "taxonomy",
                "title": categoryItem['title'],
                "url": f"{domain}/favorites/" + quote(categoryItem['title']),
                "target": "",
                "attr_title": "",
                "description": "",
                "classes": "",
                "xfn": "",
                "status": "publish",
                "original_title": categoryItem['title'],
                "nav_menu_term_id": 24,
                "_invalid": 'false',
                "type_label": "网址分类"
            }

    firstUrl = 'https://c7c.com/wp-admin/customize.php?theme=onenav&return=https://c7c.com/wp-admin/themes.php'
    rexStr = '{"save":"(.+)","preview":"(.+)","switch_themes'
    html_text = mySession.get(firstUrl)
    match = re.search(rexStr, html_text.text)

    if match:
        saveCode = match.group(1)
        previewCode = match.group(2)

        url = 'https://c7c.com/wp-admin/admin-ajax.php'
        # p = {
        #     "nav_menu_item[-5617926963124259000]": {
        #         "object_id": 92,
        #         "object": "favorites",
        #         "menu_item_parent": 0,
        #         "position": 1,
        #         "type": "taxonomy",
        #         "title": "AI常用工具",
        #         "url": f"{domain}/favorites/ai%e5%b8%b8%e7%94%a8%e5%b7%a5%e5%85%b7",
        #         "target": "",
        #         "attr_title": "",
        #         "description": "",
        #         "classes": "",
        #         "xfn": "",
        #         "status": "publish",
        #         "original_title": "AI常用工具",
        #         "nav_menu_term_id": 24,
        #         "_invalid": 'false',
        #         "type_label": "网址分类"
        #     },
        #     "nav_menu_item[-8507937094935357000]": {
        #         "object_id": 93,
        #         "object": "favorites",
        #         "menu_item_parent": -5617926963124259000,
        #         "position": 2,
        #         "type": "taxonomy",
        #         "title": "AI办公工具",
        #         "url": f"{domain}/favorites/ai%e5%8a%9e%e5%85%ac%e5%b7%a5%e5%85%b7",
        #         "target": "",
        #         "attr_title": "",
        #         "description": "",
        #         "classes": "",
        #         "xfn": "",
        #         "status": "publish",
        #         "original_title": "AI办公工具",
        #         "nav_menu_term_id": 24,
        #         "_invalid": 'false',
        #         "type_label": "网址分类"
        #     }
        # }
        data = {
            'wp_customize': 'on',
            'customize_theme': 'onenav',
            'nonce': saveCode,
            'customize_changeset_uuid': uuid.uuid4(),
            'customize_autosaved': 'on',
            'customized': json.dumps(pList, ensure_ascii=False),
            'customize_changeset_status': 'publish',
            'action': 'customize_save',
            'customize_preview_nonce': previewCode
        }
        response = mySession.post(url, data=data)

        print(response.text)


# 发布文章
# {
#         "categoryTitle": "跨境干货",
#         "categoryDesc": "facebook、instagram、whatsapp、line、telegram海外社交媒体营销，海外引流推广，快速涨粉攻略，跨境电商及出海项目经验交流，facebook和google海外广告投放技巧，外贸实用引流和营销工具，经典跨境运营案例，干货文章分享等。",
#         "title": "亚马逊云代理商|解析亚马逊云服务：企业首选的云计算平台",
#         "desc": "摘要内容"
#         "link": "https://007tg.com/2024/05/14/24261/",
#         "content": "<h1>正文<h1/>",
#         "tags": [
#             "EchoData筛号系统",
#             "全球号码数据",
#             "全球号码生成",
#             "全球号码生成工具",
#             "全球号码筛选",
#             "全球号码过滤",
#             "全球号码采集",
#             "全球随机号码生成"
#         ]
#     },
def postBlog(postData):
    # 网站的发文账户
    id = "admin"
    password = "admin123"
    url = f"{domain}/xmlrpc.php"

    which = "publish"
    # which = "draft"

    # 建立客户端
    wp = Client(url, id, password)
    content = postData['content']
    content = content.replace('007TG', '柒彩出海导航')

    tags = postData['tags']
    for i in range(len(tags)):
        tags[i] = tags[i].replace('007TG', '柒彩出海').replace('007出海', '柒彩出海')

    title = postData['title'].replace('007TG', '').replace('007出海', '柒彩出海')
    # 建立新文章
    post = WordPressPost()
    post.post_status = which
    post.title = title.replace('007TG', '')
    post.content = content
    post.excerpt = postData['desc'].replace('007TG', '柒彩出海')
    post.terms_names = {
        'category': [postData['categoryTitle']],
        "post_tag": tags
    }

    # 发表文章
    wp.call(NewPost(post))


def getPost():
    init()
    pageNum = 1
    cureentPageNum = 1
    rData = []
    while cureentPageNum <= pageNum:
        htmlTree = etree.HTML(mySession.get('https://c7c.com/wp-admin/edit.php?paged=' + str(cureentPageNum)).text)
        pageNum = int(htmlTree.xpath('//*[@id="table-paging"]/span/span/text()')[0])
        trs = htmlTree.xpath('//*[@id="the-list"]//tr')
        for tr in trs:
            posts = tr.xpath('.//strong/a/text()')
            if len(posts) > 0:
                for item in posts:
                    rData.append(
                        item
                    )
            else:
                continue
        cureentPageNum += 1
    return rData


# 初始化登陆获取cookie
def init(site = "https://c7c.com", user = "admin", pwd = "admin123"):
    global domain
    domain = site
    logger.info("开始执行初始化登陆")
    loginUrl = f"{domain}/wp-login.php"
    username = user
    password = pwd

    mySession.post(loginUrl, data={
        "log": username,
        "pwd": password,
        "wp-submit": "登录",
        "redirect_to": f"{domain}/wp-admin/",
        "testcookie": "1",
        "rememberme": "forever"
    })
    logger.info("获取到的cookie：" + str(mySession.cookies.get_dict()))


if __name__ == '__main__':
    init()
    # getPost()
    # print(getPost())

    # postBlog()
    # getCategoryAll()
    # pass
    # blogDatas = []
    # with open('outBlog.json', 'r') as file:
    #     blogDatas = json.load(file)
    # for blogData in blogDatas:
    #     postBlog(blogData)

    # postBlog()

    # init()
    # syncMenu()
    # getLinkDescAll()
    # datas = getCategoty()
    # logger.info("所有分类数据：" + json.dumps(datas))
    # logger.info("分类数量：" + str(len(datas)))
    #
    # likeDatas = getLinkDescAll()
    # logger.info("所有网址数据：" + json.dumps(likeDatas))
    # logger.info("网址数量：" + str(len(likeDatas)))

    # linkByCidDatas = getLinkDesc('37')
    # logger.info("当前分类网址数据：" + json.dumps(linkByCidDatas))
    # logger.info("当前分类网址数量：" + str(len(linkByCidDatas)))

    # 添加分类
    # addCategory(
    #     "代码测试添加分类",
    #     "test-add-category",
    #     "-1",
    #     "测试添加分类描述",
    #     "测试添加分类seo标题",
    #     "测试添加分类seo关键词",
    #     "测试添加分类seo描述",
    # )
    # 添加/修改网址
    # 测试发布 youtube。baidu。google
    # addLink(
    #     "测试添加文章-postsj",
    #     "<h1>正文描述</h1>",
    #     "http://so.com",
    #     "26",
    #     "链接描述内容",
    #     "标签1、标签2、标签3",
    #     "seo标题",
    #     "seo关键词",
    #     "seo描述",
    # )

    # addLink(
    #     "测试添加文章-post111111",
    #     "<h1>正文描述</h1>",
    #     "http://so.com",
    #     "26",
    #     "链接描述内容",
    #     "标签1、标签2、标签3",
    #     "seo标题",
    #     "seo关键词",
    #     "seo描述",
    # )

    # updateLinkInfo(
    #     '974',
    #     "修改后的标题",
    #     "<h1>修改正文</h1>",
    #     "http://baidu.com",
    #     "26",
    #     "链接描述内容",
    #     "标签5",
    #     "seo标题111",
    #     "seo关键词222",
    #     "seo关键词333",
    # )
