# -*- coding: utf-8 -*-

import scrapy
from tel.items import TelItem
from tel.item_loaders import TelItemLoader


class TelSpider(scrapy.Spider):
    name = 'tel'
    start_urls = [
        'http://baike.baidu.com/link?url=7w8P7im6dgKhsFHHLvEpvUUcoO4V2itc4eWh8OkI49hjOyBDk9uoFMnMqoxwoF7W9BQCf6-gqaI7D8TOB0D8J_'
    ]

    def parse(self, response):
        for row in response.css('.para'):
            text = row.xpath('string(.)').extract_first()
            if not text:
                continue

            text = text.strip()
            if not text.startswith('0'):
                # 跳过非“0”开关的行，比如“在中国大陆拨打国内长途电话时，要加拨长途冠码0。”这行
                continue

            if text.find(u'已') >= 0:
                # 跳过含“已”的行，这些行包含已废弃的电话区号，如“0378 开封（郑州、开封已合并使用0371）”
                continue

            # 处理沈阳、南京、武汉、成都、西安、广州等后冒号及详情说明的电话区号
            index = text.find(u'：')
            if index >= 0:
                text = text[:index]

            # 沈阳、成都、西安等已与周边城市统一区号的电话区号
            if text.find(u'（含') >= 0:
                text = text.replace(u'（含', u'、')
                text = text.replace(u'及', u'、')
                text = text.replace(u'）', '')     # 处理结尾的括号

            index = text.find(' ')
            if index == -1:
                self.logger.warn(u'无法识别的电话区号信息：%s' % text)
                continue

            code = text[:index]
            for city in text[index + 1:].split(u'、'):
                if code == '0898':   # 对海南省进行特殊处理
                    city = u'海南省'
                else:
                    city = city.replace(u'（8位）', '')

                # 处理海西─德令哈、海西─格尔木、伊犁─奎屯、伊犁─伊宁等县级市与所在地级市不一致的情况
                index = city.find(u'─')
                if index >= 0:
                    city = city[index + 1:]

                loader = TelItemLoader(TelItem(), row)
                loader.add_value('code', code)
                loader.add_value('name', city)
                yield loader.load_item()