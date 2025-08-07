# -*- coding: utf-8 -*-
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import copy
import pandas as pd


class FuncInfo(object):
    def __init__(self, code, name=None, fund_type=None):
        self.code = code                           # 基金代码
        self.name = name                           # 基金名
        self.fund_type = fund_type                 # 类型
        self._unit_value_ls = []                   # 单位净值list (字符串类型, ExtendedFuncInfo类中会转换为float类型)
        self._cumulative_value_ls = []             # 累计净值list
        self._daily_growth_rate_ls = []            # 日增长率     (字符串类型, ExtendedFuncInfo类中会转换为float类型) 
        self._purchase_state_ls = []               # 申购状态
        self._redemption_state_ls = []             # 赎回状态
        self._bonus_distribution_ls = []           # 分红送配
        self._date_ls = []                         # 交易日list (datetime类型)
        self._date2idx_map = {}                    # 交易日 -> 单位净值list/累计净值list.. idx(字典类型，键为字符串格式的日期)

    def clear_data(self):
        # 清除所有存储的数据
        self._unit_value_ls = []
        self._cumulative_value_ls = []
        self._daily_growth_rate_ls = []
        self._date_ls = []
        self._purchase_state_ls = []
        self._redemption_state_ls = []
        self._bonus_distribution_ls = []
        self._date2idx_map = {}

    @staticmethod
    def _parse_date(date, fmt):
        # 将日期转换为字符串格式
        if isinstance(date, datetime):
            date = date.strftime(fmt)
        if not isinstance(date, str):
            raise Exception("date type(%s) error, required: datetime or str" % type(date))
        return date

    def _date3idx(self, date):
        # 将日期映射到存储数据列表中的索引
        if isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")
        return self._date2idx_map.get(date)

    def get_unit_value(self, date):
        # 获取特定日期的单位净值
        idx = self._date3idx(date)
        return None if idx is None else self._unit_value_ls[idx]

    def get_cumulative_value(self, date):
        # 获取特定日期的累计净值
        idx = self._date3idx(date)
        return None if idx is None else self._cumulative_value_ls[idx]
    
    def get_purchase_state(self, date):
        # 获取特定日期的申购状态
        idx = self._date3idx(date)
        return None if idx is None else self._purchase_state_ls[idx]
    
    def get_redemption_state(self, date):
        # 获取特定日期的赎回状态
        idx = self._date3idx(date)
        return None if idx is None else self._redemption_state_ls[idx]
    
    def get_bonus_distribution(self, date):
        # 获取特定日期的分红送配
        idx = self._date3idx(date)
        return None if idx is None else self._bonus_distribution_ls[idx]

    def get_daily_growth_rate(self, date):
        # 获取特定日期的日增长率
        idx = self._date3idx(date)
        return None if idx is None else self._daily_growth_rate_ls[idx]

    def load_net_value_info(self, start_date, end_date):
        # 从指定的URL获取基金信息，并在日期范围内填充类属性
        url = "http://fund.eastmoney.com/f10/F10DataApi.aspx"
        date_fmt = "%Y-%m-%d"
        info = {
            "type": "lsjz",
            "code": self.code,
            "per": 49,
            "sdate": self._parse_date(start_date, date_fmt),
            "edate": self._parse_date(end_date, date_fmt),
        }
        page = 0
        # fp = open("./output/fund_info/%s_%s_raw.txt" % (self.code, self.name), "w")
        update_flag = True
        while update_flag:
            page = page + 1
            update_flag = False
            info["page"] = page
            r = requests.get(url, info)
            soup = BeautifulSoup(r.text, 'lxml')
            th_list = None
            for idx, tr in enumerate(soup.find_all('tr')):
                if idx == 0:
                    th_list = [x.text for x in tr.find_all("th")]
                else:
                    tds = tr.find_all('td')
                    values = [w.text for w in tds]
                    if values[0] == "暂无数据!":
                        break
                    dict_data = dict(zip(th_list, values))
                    # fp.write("%s\n" % dict_data)
                    date_str = dict_data.get("净值日期")
                    if date_str and not self._date2idx_map.get(date_str):
                        self._date2idx_map[date_str] = len(self._unit_value_ls)
                        self._unit_value_ls.append(dict_data.get("单位净值"))
                        self._cumulative_value_ls.append(dict_data.get("累计净值"))
                        # 将日期字符串转换为datetime对象
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        self._date_ls.append(date_obj)
                        self._purchase_state_ls.append(dict_data.get("申购状态"))
                        self._redemption_state_ls.append(dict_data.get("赎回状态"))
                        self._bonus_distribution_ls.append(dict_data.get("分红送配"))
                        self._daily_growth_rate_ls.append(dict_data.get("日增长率"))  
                        update_flag = True

    def get_data_frame(self):
        # 将存储的数据转换为 pandas DataFrame，以便进一步分析或导出
        date_list = self._date_ls
        df = pd.DataFrame({
            "净值日期": date_list,  # 现在是datetime类型
            "单位净值": [self.get_unit_value(date) for date in date_list],
            "累计净值": [self.get_cumulative_value(date) for date in date_list],
            "日增长率": [self.get_daily_growth_rate(date) for date in date_list],
            "申购状态": [self.get_purchase_state(date) for date in date_list],
            "赎回状态": [self.get_redemption_state(date) for date in date_list],
            "分红送配": [self.get_bonus_distribution(date) for date in date_list],
        })
        return df


if __name__ == '__main__':
    # 主执行部分：创建一个 FuncInfo 实例，加载特定日期范围内的数据，打印一些值，并将数据导出到CSV文件
    j = FuncInfo(code='007467', name="")
    j.load_net_value_info(datetime(2000, 9, 1), datetime(2029, 9, 20))
    date = "2019-09-20"
    print(j.get_unit_value(date), j.get_cumulative_value(date), j.get_daily_growth_rate(date))
    df = j.get_data_frame()
    df.to_csv("./csv_data/007467.csv")
