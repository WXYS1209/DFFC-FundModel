import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QScrollArea,
    QGroupBox, QFormLayout, QLabel, QHBoxLayout, QGridLayout, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase
from extended_funcinfo import ExtendedFuncInfo
from datetime import datetime


class FundDataWorker(QThread):
    """基金数据获取工作线程"""
    data_ready = pyqtSignal(list)
    
    def run(self):
        try:
            funds = get_all_funds()
            self.data_ready.emit(funds)
        except Exception as e:
            print(f"获取基金数据时出错: {e}")
            self.data_ready.emit([])

def get_all_funds():
    # 定义所有基金及参数
    configs = [
        {'code': '008299', 'name': '华夏中证银行ETF联接C', 'params': {'alpha': 0.0721, 'beta': 0.00939, 'gamma': 0.0398, 'season_length': 9}, 'estimate_info': {'code': '512730', 'type': 'fund'}},
        {'code': '004253', 'name': '国泰黄金ETF联接C', 'params': {'alpha': 0.111, 'beta': 0.00609, 'gamma': 0.0277, 'season_length': 14}, 'estimate_info': {'code': '518880', 'type': 'fund'}},
        {'code': '008087', 'name': '华夏5G通信ETF联接C', 'params': {'alpha': 0.100, 'beta': 0.00539, 'gamma': 0.0451, 'season_length': 10}, 'estimate_info': {'code': '515050', 'type': 'fund'}},
        {'code': '011937', 'name': '华夏阿尔法精选混合', 'params': {'alpha': 0.0740, 'beta': 0.0281, 'gamma': 0.415, 'season_length': 14}},
        {'code': '017102', 'name': '大摩数字经济混合', 'params': {'alpha': 0.0756, 'beta':0.0195, 'gamma': 0.174, 'season_length': 14}},
        {'code': '017437', 'name': '华宝纳斯达克100ETF联接C', 'params': {'alpha': 0.141, 'beta': 0.0105, 'gamma': 0.0840, 'season_length': 23}},
        {'code': '021483', 'name': '华夏低波红利ETF联接C', 'params': {'alpha': 0.0842, 'beta': 0.0121, 'gamma': 0.223, 'season_length': 22}, 'estimate_info': {'code': '159547', 'type': 'fund'}},
        {'code': '012997', 'name': '鹏华优选汇报灵活配置混合C', 'params': {'alpha': 0.1278, 'beta': 0.00807, 'gamma': 0.1861, 'season_length': 16}},
        {'code': '013360', 'name': '华夏磐泰混合(LOF)', 'params': {'alpha': 0.1129, 'beta': 0.00959, 'gamma': 0.186, 'season_length': 17}},
        {'code': '020423', 'name': '华夏中证港股通内地金融ETF联接C', 'params': {'alpha': 0.05416, 'beta': 0.01629, 'gamma': 0.1183, 'season_length': 24}, 'estimate_info': {'code': '513190', 'type': 'fund'}},
        {'code': '320016', 'name': '诺安多策略混合', 'params': {'alpha': 0.05, 'beta': 0.02, 'gamma': 0.1, 'season_length': 24}},
    ]
    funds = []
    for cfg in configs:
        fund = ExtendedFuncInfo(
            code=cfg['code'], name=cfg['name'],
            estimate_info=cfg.get('estimate_info', None)
        )
        fund.factor_holtwinters_parameter = cfg['params']
        fund.factor_cal_holtwinters()
        fund.factor_cal_holtwinters_delta_percentage()
        fund.set_info_dict()
        funds.append(fund)
    return funds


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FundModel Overview')
        self.resize(1400, 900)  # 增加窗口大小以适应表格
        # 设置白色背景风格，增大字体大小
        self.setStyleSheet("""
            * { 
                font-family: Futura; 
                font-size: 19px; 
                background-color: white;
                color: black;
            }
            QGroupBox {
                background-color: white;
                border: none;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                font-weight: bold;
                font-size: 22px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)  # 减少整体边距
        main_layout.setSpacing(5)  # 减少主布局的间距
        
        # 创建顶部控制区域
        control_layout = QHBoxLayout()
        
        # 添加开始刷新按钮
        self.refresh_button = QPushButton("开始刷新")
        self.refresh_button.setStyleSheet("font-family: Futura; font-size: 17px; padding: 8px 20px;")
        self.refresh_button.clicked.connect(self.toggle_refresh)
        control_layout.addWidget(self.refresh_button)
        
        control_layout.addStretch()  # 添加弹性空间
        
        # 创建时间显示区域
        time_layout = QVBoxLayout()
        time_layout.setSpacing(2)
        
        # 添加当前时间显示标
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignRight)
        self.time_label.setStyleSheet("font-family: Futura; font-size: 17px; color: gray; margin: 0;")
        time_layout.addWidget(self.time_label)
        
        # 添加最后更新时间标签
        self.last_update_label = QLabel("数据未更新")
        self.last_update_label.setAlignment(Qt.AlignRight)
        self.last_update_label.setStyleSheet("font-family: Futura; font-size: 17px; color: blue; margin: 0;")
        time_layout.addWidget(self.last_update_label)
        
        control_layout.addLayout(time_layout)
        
        main_layout.addLayout(control_layout)
        
        # 添加基金信息标题 - 进一步减少空白
        title_label = QLabel("基金信息一览表")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-family: Futura; font-size: 22px; font-weight: bold; margin: 0px; color: #333;")
        main_layout.addWidget(title_label)
        
        # 设置定时器更新时间显示
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新一次
        self.update_time()  # 立即更新一次
        
        # 设置数据刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.start_refresh_data)
        self.is_refreshing = False
        
        # 创建工作线程
        self.worker = None
        
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        
        self.container = QWidget()
        vbox = QVBoxLayout(self.container)
        vbox.setContentsMargins(10, 0, 10, 10)  # 进一步减少顶部边距
        
        # 初始化表格（不需要GroupBox）
        self.table_widget = QWidget()
        self.grid_layout = QGridLayout(self.table_widget)
        self.grid_layout.setSpacing(5)  # 增加表格单元格之间的间距
        self.grid_layout.setVerticalSpacing(8)  # 设置垂直间距为8
        
        self.start_refresh_data()  # 初始加载数据
        
        vbox.addWidget(self.table_widget)
        vbox.addStretch()
        
        scroll.setWidget(self.container)
        main_layout.addWidget(scroll, 1)  # 设置拉伸因子为1，让滚动区域占据剩余空间
    
    def start_refresh_data(self):
        """开始刷新数据（在工作线程中）"""
        if self.worker is not None and self.worker.isRunning():
            return  # 如果已经有线程在运行，则不启动新的
        
        self.refresh_button.setEnabled(False)  # 禁用按钮防止重复点击
        self.refresh_button.setText("刷新中...")
        
        self.worker = FundDataWorker()
        self.worker.data_ready.connect(self.on_data_ready)
        self.worker.start()
    
    def on_data_ready(self, funds):
        """当数据准备好时更新UI"""
        self.load_fund_data_with_funds(funds)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_update_label.setText(f"最后更新: {current_time}")
        
        # 恢复按钮状态
        self.refresh_button.setEnabled(True)
        if self.is_refreshing:
            self.refresh_button.setText("停止刷新")
        else:
            self.refresh_button.setText("开始刷新")
    
    def load_fund_data_with_funds(self, funds):
        """使用提供的基金数据加载到表格"""
        # 清空现有布局
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        if funds:
            # 处理表头 - 只有名称作为第一列
            col = 0
            
            # 添加表头第一行（名称）
            header_name = QLabel("基金")
            header_name.setAlignment(Qt.AlignCenter)
            header_name.setStyleSheet("font-weight: bold; font-family: Futura; font-size: 18px; color: #333; padding: 10px; border-bottom: 2px solid #ddd;")
            self.grid_layout.addWidget(header_name, 0, col)
            col += 1
            
            # 获取除code、name和estimate_isupdate外的所有键
            info_keys = [k for k in funds[0].info_dict.keys() if k not in ['code', 'name', 'estimate_isupdate']]
            
            # 添加剩余表头
            for key in info_keys:
                # 为长标题添加换行符，使表头更紧凑
                formatted_key = key
                if len(key) > 15:  # 超过15个字符就添加换行符
                    # 查找合适的位置插入换行符
                    words = key.split('_')
                    if len(words) > 1:
                        formatted_key = '\n'.join([' '.join(words[:len(words)//2]), ' '.join(words[len(words)//2:])])
                
                header_label = QLabel(formatted_key)
                header_label.setAlignment(Qt.AlignCenter)
                header_label.setStyleSheet("font-weight: bold; font-family: Futura; font-size: 18px; color: #333; padding: 10px; border-bottom: 2px solid #ddd;")
                header_label.setWordWrap(True)  # 允许换行
                self.grid_layout.addWidget(header_label, 0, col)
                col += 1
            
            # 填充基金信息行
            for row_idx, fund in enumerate(funds, 1):
                # 创建一个包含名称和代码的组合标签
                name_code_widget = QWidget()
                name_code_widget.setStyleSheet("background-color: white; padding: 8px;")
                name_code_layout = QVBoxLayout(name_code_widget)
                name_code_layout.setContentsMargins(5, 3, 5, 3)
                name_code_layout.setSpacing(2)  # 增加名称和代码之间的间距
                
                # 基金名称
                name_label = QLabel(fund.name)
                name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                name_label.setStyleSheet("font-family: Futura; font-size: 18px; font-weight: bold; background-color: transparent; margin: 0; padding: 2px 0;")
                name_code_layout.addWidget(name_label)
                
                # 基金代码（缩小字号）
                code_label = QLabel(fund.code)
                code_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                code_label.setStyleSheet("font-family: Futura; font-size: 15px; color: gray; background-color: transparent; margin: 0; padding: 2px 0;")
                name_code_layout.addWidget(code_label)
                
                self.grid_layout.addWidget(name_code_widget, row_idx, 0)
                
                # 添加其他信息项
                for col_idx, key in enumerate(info_keys, 1):
                    val = fund.info_dict.get(key, "")                    # 对浮点数值进行格式化
                    if isinstance(val, float):
                        # 对 estimate change percent 和 now change percent 只保留2位小数并添加百分号
                        if key in ['estimate_changepercent', 'now_changepercent']:
                            val_str = f"{val:.2f}%"
                        elif key in ['factor_holtwinters_estimate_delta_percentage', 'now_holtwinters_delta_percentage']:
                            val_str = f"{val*100:.0f}%"
                        elif key in ['factor_fluctuationrateCMA30']:
                            val_str = f"{val*100:.1f}%"
                        else:
                            val_str = f"{val:.3f}"
                    else:
                        val_str = str(val)
                    
                    val_label = QLabel(val_str)
                    val_label.setAlignment(Qt.AlignCenter)
                    
                    # 为涨跌幅添加颜色
                    if key in ['estimate_changepercent', 'now_changepercent'] and isinstance(val, float):
                        if val > 0:
                            val_label.setStyleSheet("font-family: Futura; font-size: 18px; color: red; font-weight: bold; background-color: white; padding: 8px;")
                        elif val < 0:
                            val_label.setStyleSheet("font-family: Futura; font-size: 18px; color: green; font-weight: bold; background-color: white; padding: 8px;")
                        else:
                            val_label.setStyleSheet("font-family: Futura; font-size: 18px; background-color: white; padding: 8px;")
                    else:
                        val_label.setStyleSheet("font-family: Futura; font-size: 18px; background-color: white; padding: 8px;")
                    
                    self.grid_layout.addWidget(val_label, row_idx, col_idx)

    def toggle_refresh(self):
        """切换刷新状态"""
        if self.is_refreshing:
            # 停止刷新
            self.refresh_timer.stop()
            self.refresh_button.setText("开始刷新")
            self.is_refreshing = False
        else:
            # 开始刷新
            self.refresh_timer.start(120000)  # 每30秒(0.5分钟)刷新一次
            self.refresh_button.setText("停止刷新")
            self.is_refreshing = True
            self.start_refresh_data()  # 立即刷新一次
    
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"当前时间: {current_time}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用级别的Futura字体
    font = QFont("Futura", 18)  # 将字体大小设置为18
    app.setFont(font)
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
