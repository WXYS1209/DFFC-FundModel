# -*- coding: utf-8 -*-

from stock_net_value_crawler import StockNetValueCrawler
def quick_test(codenum='000001', type='stock'):
    crawler = StockNetValueCrawler()
    # 1. 获取单个股票数据
    data = crawler.get_single_data(codenum, type)
    if data:
        print(f"   {data['name']} ({data['code']})")
        print(f"   当前价: {data['current_price']:.3f} 元")
        print(f"   涨跌幅: {data['change_percent']:+.2f}%")
        print(f"   数据源: {data['source']}")
        print(f"   更新时间: {data['update_time']}")
        return data['change_percent']
    else:
        print("   获取失败")
    
if __name__ == "__main__":
    # 运行测试
    quick_test('159547','fund')
    print("\n测试完成！")
