import pymysql
import urllib.parse
from pypinyin import pinyin, Style

# 连接到 MySQL 数据库
connection = pymysql.connect(
    host='127.0.0.1',
    user='wordpress_demo',
    password='PdxpEDDGPf',
    database='wordpress_demo',
    charset='utf8mb4'
)

def chinese_to_pinyin(text):
    # 将中文转换为拼音
    pinyin_list = pinyin(text, style=Style.NORMAL)
    return ''.join([item[0] for item in pinyin_list])

try:
    with connection.cursor() as cursor:
        # 查询 wp_terms 表中的 slug 字段内容
        sql_select = "SELECT term_id, slug FROM wp_terms"
        cursor.execute(sql_select)
        results = cursor.fetchall()

        for row in results:
            term_id, slug = row
            # URL 解码
            decoded_slug = urllib.parse.unquote(slug)
            # 替换中文为拼音
            new_slug = chinese_to_pinyin(decoded_slug)
            # 更新 slug 字段的值
            sql_update = "UPDATE wp_terms SET slug = %s WHERE term_id = %s"
            cursor.execute(sql_update, (new_slug, term_id))

        # 提交更改
        connection.commit()

finally:
    # 关闭数据库连接
    connection.close()
