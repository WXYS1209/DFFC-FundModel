import sys
import json
import copy
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QScrollArea,
    QGroupBox, QFormLayout, QLabel, QHBoxLayout, QGridLayout, QPushButton, QFileDialog,
    QDialog, QLineEdit, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QFontDatabase
from source.extended_funcinfo import ExtendedFuncInfo
from datetime import datetime


class FundDataWorker(QThread):
    """基金数据刷新工作线程 - 单独的数据处理线程，与GUI线程分离"""
    data_ready = pyqtSignal(list)  # 返回完整的基金数据列表
    progress_update = pyqtSignal(str)  # 进度更新信号
    fund_processed = pyqtSignal(str, dict)  # 单个基金处理完成信号 (基金代码, 基金信息字典)
    
    def __init__(self, configs, parent=None):
        super().__init__(parent)
        self.configs = copy.deepcopy(configs)
        self._stop_requested = False
    
    def request_stop(self):
        """请求停止线程"""
        self._stop_requested = True
    
    def run(self):
        try:
            funds = []
            total = len(self.configs)
            
            self.progress_update.emit(f"开始处理 {total} 个基金...")
            
            for i, cfg in enumerate(self.configs):
                # 检查是否请求停止
                if self._stop_requested:
                    self.progress_update.emit("数据刷新已停止")
                    return
                
                try:
                    self.progress_update.emit(f"正在处理: {cfg['code']} ({i+1}/{total})")
                    fund = create_fund_from_config(cfg)
                    if fund is not None:
                        funds.append(fund)
                        # 发送单个基金处理完成的信号，供GUI实时更新
                        self.fund_processed.emit(cfg['code'], fund.info_dict)
                    else:
                        self.progress_update.emit(f"处理失败: {cfg['code']}")
                except Exception as e:
                    print(f"处理基金{cfg.get('code', 'unknown')}失败: {e}")
                    self.progress_update.emit(f"处理失败: {cfg.get('code', 'unknown')} - {str(e)}")
                    continue
            
            # 发送完整数据
            self.progress_update.emit(f"完成处理 {len(funds)} 个基金")
            self.data_ready.emit(funds)
            
        except Exception as e:
            print(f"获取基金数据时出错: {e}")
            self.progress_update.emit(f"数据获取失败: {str(e)}")
            self.data_ready.emit([])

def get_all_funds():
    # 默认启动不加载任何基金
    return []


def create_fund_from_config(cfg):
    """从配置创建基金对象（同步方式）"""
    try:
        # 确保estimate_info有正确的默认值，使用深拷贝避免修改原始配置
        cfg_copy = copy.deepcopy(cfg)
        estimate_info = copy.deepcopy(cfg_copy.get('estimate_info', {'code': '', 'type': ''}))
        
        fund = ExtendedFuncInfo(
            code=cfg_copy['code'], 
            name=cfg_copy['name'],
            estimate_info=estimate_info
        )
        
        # 从网络加载数据
        fund.load_data_net()
        
        # 获取下一日估计值
        fund.load_estimate_net()
        
        # 设置HoltWinters参数，使用深拷贝保护原始参数
        fund.factor_holtwinters_parameter = copy.deepcopy(cfg_copy['params'])
        
        # 计算HoltWinters因子和增量百分比
        fund.factor_cal_holtwinters()
        fund.factor_cal_holtwinters_delta_percentage()
        
        # 计算30日中心移动平均
        fund.factor_CMA30 = fund.factor_cal_CMA(30)
        
        # 计算波动率比率
        fund.factor_fluctuationrateCMA30 = fund.factor_cal_fluctuationrateCMA30()
        
        # 设置信息字典
        fund.set_info_dict()
        return fund
    except Exception as e:
        print(f"创建基金对象失败 {cfg.get('code', 'unknown')}: {e}")
        return None
    """添加/编辑基金信息弹窗"""
    def __init__(self, parent=None, fund_cfg=None):
        super().__init__(parent)
        self.setWindowTitle("添加/编辑基金")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        self.inputs = {}
        # 基本字段
        for key in ["code", "name"]:
            le = QLineEdit()
            if fund_cfg and key in fund_cfg:
                le.setText(str(fund_cfg[key]))
            layout.addRow(f"{key}", le)
            self.inputs[key] = le
        # 参数字段
        self.param_inputs = {}
        param_keys = ["alpha", "beta", "gamma", "season_length"]
        default_params = {"alpha": 0.07, "beta": 0.009, "gamma": 0.04, "season_length": 14}
        for k in param_keys:
            le = QLineEdit()
            if fund_cfg and "params" in fund_cfg and k in fund_cfg["params"]:
                le.setText(str(fund_cfg["params"][k]))
            elif not fund_cfg:
                le.setText(str(default_params[k]))
                le.setStyleSheet("color:gray;")
            # 修改事件绑定：明确接收 text 参数，防止覆盖 le 对象
            def on_text_changed(text, le=le, k=k):
                if text == str(default_params[k]):
                    le.setStyleSheet("color:gray;")
                else:
                    le.setStyleSheet("color:black;")
            le.textChanged.connect(on_text_changed)
            layout.addRow(f"参数-{k}", le)
            self.param_inputs[k] = le
        # 估值信息
        self.estimate_code = QLineEdit()
        self.estimate_type = QComboBox(); self.estimate_type.addItems(["fund", "stock", "none"])
        if fund_cfg and "estimate_info" in fund_cfg:
            self.estimate_code.setText(str(fund_cfg["estimate_info"].get("code", "")))
            idx = self.estimate_type.findText(fund_cfg["estimate_info"].get("type", "fund"))
            if idx >= 0: self.estimate_type.setCurrentIndex(idx)
        layout.addRow("估值代码", self.estimate_code)
        layout.addRow("估值类型", self.estimate_type)
        # 按钮
        btns = QHBoxLayout()
        ok_btn = QPushButton("确定"); ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消"); cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn); btns.addWidget(cancel_btn)
        layout.addRow(btns)

    def get_fund_cfg(self):
        code = self.inputs["code"].text().strip()
        name = self.inputs["name"].text().strip()
        params = {}
        for k, le in self.param_inputs.items():
            try:
                params[k] = float(le.text()) if k != "season_length" else int(le.text())
            except Exception:
                params[k] = 0
        est_code = self.estimate_code.text().strip()
        est_type = self.estimate_type.currentText()
        estimate_info = {"code": est_code, "type": est_type} if est_code else None
        cfg = {"code": code, "name": name, "params": params}
        if estimate_info and est_code:
            cfg["estimate_info"] = estimate_info
        return cfg


class FundEditDialog(QDialog):
    """添加/编辑基金信息弹窗"""
    def __init__(self, parent=None, fund_cfg=None):
        super().__init__(parent)
        self.setWindowTitle("添加/编辑基金")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        self.inputs = {}
        # 基本字段
        for key in ["code", "name"]:
            le = QLineEdit()
            if fund_cfg and key in fund_cfg:
                le.setText(str(fund_cfg[key]))
            layout.addRow(f"{key}", le)
            self.inputs[key] = le
        # 参数字段
        self.param_inputs = {}
        param_keys = ["alpha", "beta", "gamma", "season_length"]
        default_params = {"alpha": 0.07, "beta": 0.009, "gamma": 0.04, "season_length": 14}
        for k in param_keys:
            le = QLineEdit()
            if fund_cfg and "params" in fund_cfg and k in fund_cfg["params"]:
                le.setText(str(fund_cfg["params"][k]))
            elif not fund_cfg:
                le.setText(str(default_params[k]))
                le.setStyleSheet("color:gray;")
            # 修改事件绑定：明确接收 text 参数，防止覆盖 le 对象
            def on_text_changed(text, le=le, k=k):
                if text == str(default_params[k]):
                    le.setStyleSheet("color:gray;")
                else:
                    le.setStyleSheet("color:black;")
            le.textChanged.connect(on_text_changed)
            layout.addRow(f"参数-{k}", le)
            self.param_inputs[k] = le
        # 估值信息
        self.estimate_code = QLineEdit()
        self.estimate_type = QComboBox(); self.estimate_type.addItems(["fund", "stock", "none"])
        if fund_cfg and "estimate_info" in fund_cfg:
            self.estimate_code.setText(str(fund_cfg["estimate_info"].get("code", "")))
            idx = self.estimate_type.findText(fund_cfg["estimate_info"].get("type", "fund"))
            if idx >= 0: self.estimate_type.setCurrentIndex(idx)
        layout.addRow("估值代码", self.estimate_code)
        layout.addRow("估值类型", self.estimate_type)
        # 按钮
        btns = QHBoxLayout()
        ok_btn = QPushButton("确定"); ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消"); cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn); btns.addWidget(cancel_btn)
        layout.addRow(btns)

    def get_fund_cfg(self):
        code = self.inputs["code"].text().strip()
        name = self.inputs["name"].text().strip()
        params = {}
        for k, le in self.param_inputs.items():
            try:
                params[k] = float(le.text()) if k != "season_length" else int(le.text())
            except Exception:
                params[k] = 0
        est_code = self.estimate_code.text().strip()
        est_type = self.estimate_type.currentText()
        estimate_info = {"code": est_code, "type": est_type} if est_code else None
        cfg = {"code": code, "name": name, "params": params}
        if estimate_info and est_code:
            cfg["estimate_info"] = estimate_info

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FundModel Overview')
        self.resize(1400, 900)  # 增加窗口大小以适应表格
        
        # 简化的缓存机制
        self.fund_cache = {}  # 缓存基金对象
        self.cache_timestamp = {}  # 缓存时间戳
        self.cache_timeout = 60  # 缓存60秒
        
        # 线程状态管理（GUI主线程 + 数据工作线程）
        self.is_refreshing = False
        self.data_worker = None  # 数据刷新工作线程
        
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
        
        # 添加导入配置按钮
        self.import_button = QPushButton("导入基金配置")
        self.import_button.setStyleSheet("font-family: Futura; font-size: 17px; padding: 8px 20px;")
        self.import_button.clicked.connect(self.import_fund_config)
        control_layout.insertWidget(0, self.import_button)
        
        # 添加导出配置按钮
        self.export_button = QPushButton("导出基金配置")
        self.export_button.setStyleSheet("font-family: Futura; font-size: 17px; padding: 8px 20px;")
        self.export_button.clicked.connect(self.export_fund_config)
        control_layout.insertWidget(1, self.export_button)
        
        # 添加添加/编辑基金按钮
        self.edit_button = QPushButton("添加/编辑基金")
        self.edit_button.setStyleSheet("font-family: Futura; font-size: 17px; padding: 8px 20px;")
        self.edit_button.clicked.connect(self.open_edit_fund_dialog)
        control_layout.insertWidget(2, self.edit_button)
        
        control_layout.addStretch()  # 添加弹性空间
        
        # 创建时间显示区域
        time_layout = QVBoxLayout()
        time_layout.setSpacing(2)
        
        # 添加当前时间显示标签
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignRight)
        self.time_label.setStyleSheet("font-family: Futura; font-size: 17px; color: gray; margin: 0;")
        time_layout.addWidget(self.time_label)
        
        # 添加最后更新时间标签
        self.last_update_label = QLabel("数据未更新")
        self.last_update_label.setAlignment(Qt.AlignRight)
        self.last_update_label.setStyleSheet("font-family: Futura; font-size: 17px; color: blue; margin: 0;")
        time_layout.addWidget(self.last_update_label)
        
        # 添加进度显示标签
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignRight)
        self.progress_label.setStyleSheet("font-family: Futura; font-size: 14px; color: #666; margin: 0;")
        time_layout.addWidget(self.progress_label)
        
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
        self.refresh_timer.timeout.connect(lambda: self.start_refresh_data(force_refresh=True))
        
        # 初始化基金配置
        self.fund_configs = []
        
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
    
    def start_refresh_data(self, force_refresh=False):
        """开始刷新数据（GUI主线程 + 数据工作线程模式）"""
        # 检查是否已有工作线程在运行
        if self.data_worker is not None and self.data_worker.isRunning():
            return  # 如果已经有线程在运行，则不启动新的
        
        # 设置强制刷新标志
        self.force_refresh = force_refresh
        
        self.refresh_button.setEnabled(False)  # 禁用按钮防止重复点击
        self.refresh_button.setText("刷新中...")
        
        # 检查是否有配置
        has_configs = hasattr(self, 'fund_configs') and self.fund_configs
        
        if has_configs:
            # 启动数据工作线程
            configs = copy.deepcopy(self.fund_configs)
            self.data_worker = FundDataWorker(configs)
            
            # 连接信号
            self.data_worker.data_ready.connect(self.on_data_ready)
            self.data_worker.progress_update.connect(self.on_progress_update)
            self.data_worker.fund_processed.connect(self.on_fund_processed)
            
            # 启动线程
            self.data_worker.start()
        else:
            # 没有配置时显示空数据
            self.on_data_ready([])

    def on_data_ready(self, funds):
        """当所有数据准备好时更新UI（在GUI主线程中执行）"""
        self.load_fund_data_with_funds(funds)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_update_label.setText(f"最后更新: {current_time}")
        
        # 清空进度显示
        self.progress_label.setText("")
        
        # 恢复按钮状态
        self.refresh_button.setEnabled(True)
        if self.is_refreshing:
            self.refresh_button.setText("停止刷新")
        else:
            self.refresh_button.setText("开始刷新")
        
        # 清理线程引用
        self.data_worker = None

    def on_progress_update(self, message):
        """处理进度更新（在GUI主线程中执行）"""
        self.progress_label.setText(message)
        print(f"进度更新: {message}")

    def on_fund_processed(self, fund_code, fund_info):
        """当单个基金处理完成时的回调（可选，用于实时更新）"""
        # 这里可以实现实时更新单个基金的显示
        # 目前简单打印，可以根据需要扩展
        print(f"基金 {fund_code} 处理完成")
    
    def load_fund_data_with_funds(self, funds):
        # 清空现有布局
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not funds:
            # 如果没有基金数据，显示空状态
            empty_label = QLabel("暂无基金数据")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("font-family: Futura; font-size: 20px; color: #888; padding: 50px;")
            self.grid_layout.addWidget(empty_label, 0, 0)
            return
            
        col = 0
        header_name = QLabel("基金")
        header_name.setAlignment(Qt.AlignCenter)
        header_name.setStyleSheet("font-weight: bold; font-family: Futura; font-size: 18px; color: #333; padding: 10px; border-bottom: 2px solid #ddd;")
        self.grid_layout.addWidget(header_name, 0, col)
        col += 1
        
        # 获取表头字段并调整顺序，排除不需要的字段
        info_keys = [k for k in funds[0].info_dict.keys() if k not in ['code', 'name', 'estimate_isupdate', 'estimate_date', 'estimate_able']]
        if 'now_date' in info_keys:
            info_keys.remove('now_date')
            info_keys.insert(0, 'now_date')
        if 'now_changepercent' in info_keys:
            info_keys.remove('now_changepercent')
            info_keys.insert(1, 'now_changepercent')
        # 如果存在昨日HDP，则放在当前HDP后面
        if 'yesterday_holtwinters_delta_percentage' in info_keys:
            info_keys.remove('yesterday_holtwinters_delta_percentage')
            if 'now_holtwinters_delta_percentage' in info_keys:
                idx = info_keys.index('now_holtwinters_delta_percentage')
                info_keys.insert(idx+1, 'yesterday_holtwinters_delta_percentage')
            else:
                info_keys.append('yesterday_holtwinters_delta_percentage')
        # 修改表头：映射对应键为中文
        for key in info_keys:
            key_for_display = key
            if key == 'now_date':
                key_for_display = '净值日期'
            elif key == 'now_changepercent':
                key_for_display = '净值变化'
            elif key == 'estimate_changepercent':
                key_for_display = '今日估值'
            elif key == 'now_holtwinters_delta_percentage':
                key_for_display = '当前HDP'
            elif key == 'yesterday_holtwinters_delta_percentage':
                key_for_display = '昨日HDP'
            elif key == 'factor_holtwinters_estimate_delta_percentage':
                key_for_display = '估值HDP'
            elif key == 'factor_fluctuationrateCMA30':
                key_for_display = '波动率CMA30'
            formatted_key = key_for_display
            if len(key_for_display) > 15:
                words = key_for_display.split('_')
                if len(words) > 1:
                    formatted_key = '\n'.join([' '.join(words[:len(words)//2]), ' '.join(words[len(words)//2:])])
            if key == 'estimate_changepercent':
                today_str = datetime.now().strftime("(%Y-%m-%d)")
                formatted_key = f"{formatted_key}<br/><span style='color:#888;font-size:14px;margin-top:6px;display:inline-block;'>{today_str}</span>"
                header_label = QLabel()
                header_label.setTextFormat(Qt.RichText)
                header_label.setText(formatted_key)
            elif key == 'factor_holtwinters_estimate_delta_percentage':
                today_str = datetime.now().strftime("(%Y-%m-%d)")
                formatted_key = f"{formatted_key}<br/><span style='color:#888;font-size:14px;margin-top:6px;display:inline-block;'>{today_str}</span>"
                header_label = QLabel()
                header_label.setTextFormat(Qt.RichText)
                header_label.setText(formatted_key)
            else:
                header_label = QLabel(formatted_key)
            header_label.setAlignment(Qt.AlignCenter)
            header_label.setStyleSheet("font-weight: bold; font-family: Futura; font-size: 18px; color: #333; padding: 10px; border-bottom: 2px solid #ddd;")
            header_label.setWordWrap(True)
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
            name_label = QLabel(fund.info_dict.get('name', ''))
            name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            name_label.setStyleSheet("font-family: Futura; font-size: 18px; font-weight: bold; background-color: transparent; margin: 0; padding: 2px 0;")
            name_code_layout.addWidget(name_label)
            
            # 基金代码（缩小字号）
            code_label = QLabel(fund.info_dict.get('code', ''))
            code_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            code_label.setStyleSheet("font-family: Futura; font-size: 15px; color: gray; background-color: transparent; margin: 0; padding: 2px 0;")
            name_code_layout.addWidget(code_label)
            
            self.grid_layout.addWidget(name_code_widget, row_idx, 0)
            
            # 添加其他信息项
            for col_idx, key in enumerate(info_keys, 1):
                val = fund.info_dict.get(key, "")
                if isinstance(val, float):
                    if key in ['estimate_changepercent', 'now_changepercent']:
                        val_str = f"{val:.2f}%"
                    elif key in ['factor_holtwinters_estimate_delta_percentage', 'now_holtwinters_delta_percentage']:
                        val_str = f"{val*100:.0f}%"
                    elif key == 'yesterday_holtwinters_delta_percentage':
                        val_str = f"{val*100:.0f}%"
                    elif key in ['factor_fluctuationrateCMA30']:
                        val_str = f"{val*100:.1f}%"
                    else:
                        val_str = f"{val:.3f}"
                else:
                    val_str = str(val)
                
                val_label = QLabel(val_str)
                val_label.setAlignment(Qt.AlignCenter)
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

    def clear_cache(self):
        """清除基金对象缓存"""
        self.fund_cache.clear()
        self.cache_timestamp.clear()
    
    def create_fund_with_cache(self, cfg, force_refresh=False):
        """创建基金对象，支持缓存"""
        # 生成缓存键
        cache_key = f"{cfg['code']}_{cfg.get('estimate_info', {}).get('code', '')}"
        current_time = datetime.now()
        
        # 检查缓存（除非强制刷新）
        if not force_refresh and cache_key in self.fund_cache and cache_key in self.cache_timestamp:
            if (current_time - self.cache_timestamp[cache_key]).total_seconds() < self.cache_timeout:
                return copy.deepcopy(self.fund_cache[cache_key])
        
        # 创建新的基金对象
        fund = create_fund_from_config(cfg)
        
        if fund is not None:
            # 缓存基金对象
            self.fund_cache[cache_key] = copy.deepcopy(fund)
            self.cache_timestamp[cache_key] = current_time
        
        return fund

    def toggle_refresh(self):
        """切换刷新状态"""
        if self.is_refreshing:
            # 停止刷新
            self.refresh_timer.stop()
            
            # 停止运行中的数据工作线程
            if self.data_worker is not None and self.data_worker.isRunning():
                self.data_worker.request_stop()  # 使用优雅的停止方式
                self.data_worker.wait(3000)  # 等待最多3秒
                if self.data_worker.isRunning():
                    self.data_worker.terminate()  # 如果还在运行则强制终止
                    self.data_worker.wait()
                self.data_worker = None
            
            self.clear_cache()  # 清除缓存，确保下次刷新获取最新数据
            self.refresh_button.setText("开始刷新")
            self.refresh_button.setEnabled(True)
            self.is_refreshing = False
            self.last_update_label.setText("已停止刷新")
            self.progress_label.setText("")  # 清空进度显示
        else:
            # 开始刷新前清除缓存，确保获取最新数据
            self.clear_cache()
            # 开始刷新
            self.refresh_timer.start(120000)  # 每2分钟刷新一次
            self.refresh_button.setText("停止刷新")
            self.is_refreshing = True
            self.start_refresh_data(force_refresh=True)  # 立即强制刷新一次
    
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"当前时间: {current_time}")
    
    def import_fund_config(self):
        """导入基金配置文件并刷新表格"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择基金配置文件", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                configs = json.load(f)
            
            # 更新配置
            self.fund_configs = copy.deepcopy(configs)
            
            # 清除缓存并启动数据刷新
            self.clear_cache()
            self.start_refresh_data(force_refresh=True)
            self.last_update_label.setText("已从配置文件导入基金")
        except Exception as e:
            self.last_update_label.setText(f"导入失败: {e}")

    def export_fund_config(self):
        """导出当前基金配置到JSON文件"""
        file_path, _ = QFileDialog.getSaveFileName(self, "导出基金配置", "fund_config.json", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.fund_configs, f, ensure_ascii=False, indent=2)
            self.last_update_label.setText("已导出基金配置")
        except Exception as e:
            self.last_update_label.setText(f"导出失败: {e}")

    def open_edit_fund_dialog(self):
        """弹出添加/编辑基金窗口"""
        if not hasattr(self, 'fund_configs') or self.fund_configs is None:
            self.fund_configs = []
        
        dlg = FundEditDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            new_cfg = dlg.get_fund_cfg()
            
            # 检查是否是编辑现有基金
            fund_updated = False
            for i, cfg in enumerate(self.fund_configs):
                if cfg['code'] == new_cfg['code']:
                    self.fund_configs[i] = copy.deepcopy(new_cfg)
                    fund_updated = True
                    break
            
            if fund_updated:
                # 编辑已存在基金，清除相关缓存
                cache_key = f"{new_cfg['code']}_{new_cfg.get('estimate_info', {}).get('code', '')}"
                if cache_key in self.fund_cache:
                    del self.fund_cache[cache_key]
                if cache_key in self.cache_timestamp:
                    del self.cache_timestamp[cache_key]
                self.last_update_label.setText(f"已编辑基金: {new_cfg['code']}")
            else:
                # 新增基金
                self.fund_configs.append(copy.deepcopy(new_cfg))
                self.insert_new_fund_row(new_cfg)
                self.last_update_label.setText(f"已添加基金: {new_cfg['code']}")

    def get_display_info_keys(self, fund_info_dict):
        """根据基金信息字典获取用于显示的字段列表，按固定顺序排列"""
        # 获取实际字段并调整顺序（与表头保持一致），排除不需要的字段
        info_keys = [k for k in fund_info_dict.keys() if k not in ['code', 'name', 'estimate_isupdate', 'estimate_date', 'estimate_able']]
        
        # 按固定顺序排列
        ordered_keys = []
        
        # 优先显示的字段（按顺序）
        priority_fields = [
            'now_date', 
            'now_changepercent', 
            'estimate_changepercent',
            'now_holtwinters_delta_percentage', 
            'yesterday_holtwinters_delta_percentage',
            'factor_holtwinters_estimate_delta_percentage',
            'factor_fluctuationrateCMA30'
        ]
        
        # 按优先级添加存在的字段
        for field in priority_fields:
            if field in info_keys:
                ordered_keys.append(field)
                info_keys.remove(field)
        
        # 添加剩余字段
        ordered_keys.extend(info_keys)
        
        return ordered_keys

    def get_default_info_keys(self):
        """获取默认的字段列表（当无法动态获取时使用）"""
        return [
            'now_date', 
            'now_changepercent', 
            'estimate_changepercent',
            'now_holtwinters_delta_percentage', 
            'yesterday_holtwinters_delta_percentage',
            'factor_fluctuationrateCMA30'
        ]

    def insert_new_fund_row(self, cfg):
        """添加新基金行（启动数据刷新）"""
        # 启动数据刷新以更新整个表格
        self.start_refresh_data(force_refresh=True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用级别的Futura字体
    font = QFont("Futura", 18)  # 将字体大小设置为18
    app.setFont(font)
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())