import sys
import json
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
    # 默认启动不加载任何基金
    return []


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
        return cfg


class FundDetailWorker(QThread):
    fund_ready = pyqtSignal(int, object)  # index, fund_obj
    def __init__(self, cfg, idx, main_window):
        super().__init__()
        self.cfg = cfg
        self.idx = idx
        self.main_window = main_window
    def run(self):
        try:
            # 如果是强制刷新模式，跳过缓存直接创建新对象
            if hasattr(self.main_window, 'force_refresh') and self.main_window.force_refresh:
                fund = self.create_new_fund()
                self.fund_ready.emit(self.idx, fund)
                return
            
            # 生成缓存键
            cache_key = f"{self.cfg['code']}_{self.cfg.get('estimate_info', {}).get('code', '')}"
            current_time = datetime.now()
            
            # 检查缓存是否存在且未过期
            if (cache_key in self.main_window.fund_cache and 
                cache_key in self.main_window.cache_timestamp and
                (current_time - self.main_window.cache_timestamp[cache_key]).total_seconds() < self.main_window.cache_timeout):
                # 使用缓存的基金对象
                fund = self.main_window.fund_cache[cache_key]
                self.fund_ready.emit(self.idx, fund)
                return
            
            # 创建新的基金对象
            fund = self.create_new_fund()
            
            # 缓存基金对象
            self.main_window.fund_cache[cache_key] = fund
            self.main_window.cache_timestamp[cache_key] = current_time
            
            self.fund_ready.emit(self.idx, fund)
        except Exception as e:
            print(f"FundDetailWorker error for {self.cfg.get('code', 'unknown')}: {e}")
            self.fund_ready.emit(self.idx, None)
    
    def create_new_fund(self):
        """创建新的基金对象"""
        # 确保estimate_info有正确的默认值
        estimate_info = self.cfg.get('estimate_info', {'code': '', 'type': ''})
        
        fund = ExtendedFuncInfo(
            code=self.cfg['code'], 
            name=self.cfg['name'],
            estimate_info=estimate_info
        )
        fund.factor_holtwinters_parameter = self.cfg['params']
        fund.factor_cal_holtwinters()
        fund.factor_cal_holtwinters_delta_percentage()
        fund.set_info_dict()
        return fund

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FundModel Overview')
        self.resize(1400, 900)  # 增加窗口大小以适应表格
        
        # 添加基金对象缓存
        self.fund_cache = {}  # 缓存基金对象
        self.cache_timestamp = {}  # 缓存时间戳
        self.cache_timeout = 60  # 缓存60秒
        
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
        self.is_refreshing = False
        
        # 创建工作线程
        self.worker = None
        
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
        """开始刷新数据（在工作线程中）"""
        if self.worker is not None and self.worker.isRunning():
            return  # 如果已经有线程在运行，则不启动新的
        
        # 设置强制刷新标志
        self.force_refresh = force_refresh
        
        self.refresh_button.setEnabled(False)  # 禁用按钮防止重复点击
        self.refresh_button.setText("刷新中...")
        
        # 如果有配置文件数据，使用配置文件刷新，否则使用默认方式
        if hasattr(self, 'fund_configs') and self.fund_configs:
            self.refresh_fund_table()
            # 恢复按钮状态
            self.refresh_button.setEnabled(True)
            if self.is_refreshing:
                self.refresh_button.setText("停止刷新")
            else:
                self.refresh_button.setText("开始刷新")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.last_update_label.setText(f"最后更新: {current_time}")
        else:
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
        # 清空现有布局
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        if funds:
            col = 0
            header_name = QLabel("基金")
            header_name.setAlignment(Qt.AlignCenter)
            header_name.setStyleSheet("font-weight: bold; font-family: Futura; font-size: 18px; color: #333; padding: 10px; border-bottom: 2px solid #ddd;")
            self.grid_layout.addWidget(header_name, 0, col)
            col += 1
            
            # 获取表头字段并调整顺序
            info_keys = [k for k in funds[0].info_dict.keys() if k not in ['code', 'name', 'estimate_isupdate', 'estimate_date']]
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
    
    def create_temp_fund(self, temp_cfg):
        """创建临时基金对象用于获取表头字段"""
        # 确保estimate_info有正确的默认值
        estimate_info = temp_cfg.get('estimate_info', {'code': '', 'type': ''})
        temp_fund = ExtendedFuncInfo(
            code=temp_cfg['code'],
            name=temp_cfg['name'],
            estimate_info=estimate_info
        )
        temp_fund.factor_holtwinters_parameter = temp_cfg['params']
        temp_fund.factor_cal_holtwinters()
        temp_fund.factor_cal_holtwinters_delta_percentage()
        temp_fund.set_info_dict()
        return temp_fund

    def toggle_refresh(self):
        """切换刷新状态"""
        if self.is_refreshing:
            # 停止刷新
            self.refresh_timer.stop()
            self.refresh_button.setText("开始刷新")
            self.is_refreshing = False
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
            self.fund_configs = configs
            self.refresh_fund_table()
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
        if not hasattr(self, 'fund_rows') or self.fund_rows is None:
            self.fund_rows = []
        dlg = FundEditDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            new_cfg = dlg.get_fund_cfg()
            for i, cfg in enumerate(self.fund_configs):
                if cfg['code'] == new_cfg['code']:
                    self.fund_configs[i] = new_cfg
                    # 编辑已存在基金，直接更新fund_configs，不刷新表格
                    self.last_update_label.setText(f"已编辑基金: {new_cfg['code']}")
                    return
            # 新增基金，插入表格最后一行并异步加载
            self.fund_configs.append(new_cfg)
            self.insert_new_fund_row(new_cfg)
            self.last_update_label.setText(f"已添加基金: {new_cfg['code']}")

    def insert_new_fund_row(self, cfg):
        info_keys = [
            'now_date', 'now_changepercent', 'estimate_changepercent',
            'now_holtwinters_delta_percentage', 'yesterday_holtwinters_delta_percentage',
            'factor_fluctuationrateCMA30'
        ]
        # 在表格最后插入新基金一行，先显示Loading...，再异步加载
        row_idx = len(self.fund_rows) + 1
        row_widgets = []
        name_code_widget = QWidget()
        name_code_widget.setStyleSheet("background-color: white; padding: 8px;")
        name_code_layout = QVBoxLayout(name_code_widget)
        name_code_layout.setContentsMargins(5, 3, 5, 3)
        name_code_layout.setSpacing(2)
        name_label = QLabel(cfg['name'])
        name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        name_label.setStyleSheet("font-family: Futura; font-size: 18px; font-weight: bold; background-color: transparent; margin: 0; padding: 2px 0;")
        name_code_layout.addWidget(name_label)
        code_label = QLabel(cfg['code'])
        code_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        code_label.setStyleSheet("font-family: Futura; font-size: 15px; color: gray; background-color: transparent; margin: 0; padding: 2px 0;")
        name_code_layout.addWidget(code_label)
        self.grid_layout.addWidget(name_code_widget, row_idx, 0)
        row_widgets.append(name_code_widget)
        for col_idx in range(1, len(info_keys)+1):
            val_label = QLabel("Loading...")
            val_label.setAlignment(Qt.AlignCenter)
            val_label.setStyleSheet("font-family: Futura; font-size: 18px; color: #888; background-color: white; padding: 8px;")
            self.grid_layout.addWidget(val_label, row_idx, col_idx)
            row_widgets.append(val_label)
        self.fund_rows.append(row_widgets)
        # 启动异步加载
        worker = FundDetailWorker(cfg, len(self.fund_rows)-1, self)
        worker.fund_ready.connect(self.on_fund_detail_ready)
        if not hasattr(self, 'fund_workers'):
            self.fund_workers = []
        self.fund_workers.append(worker)
        worker.start()

    def refresh_fund_table(self):
        # 用当前 self.fund_configs 刷新表格，先显示Loading...
        funds = [None] * len(self.fund_configs)
        self.load_fund_data_with_funds_loading(self.fund_configs, funds)
        # 启动每只基金的异步加载
        if not hasattr(self, 'fund_workers'):
            self.fund_workers = []
        # 停止之前的worker
        for worker in self.fund_workers:
            if worker.isRunning():
                worker.quit()
                worker.wait()
        self.fund_workers = []
        for idx, cfg in enumerate(self.fund_configs):
            worker = FundDetailWorker(cfg, idx, self)
            worker.fund_ready.connect(self.on_fund_detail_ready)
            self.fund_workers.append(worker)
            worker.start()

    def load_fund_data_with_funds_loading(self, configs, funds):
        # 清空现有布局
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        self.fund_rows = []
        if configs:
            col = 0
            header_name = QLabel("基金")
            header_name.setAlignment(Qt.AlignCenter)
            header_name.setStyleSheet("font-weight: bold; font-family: Futura; font-size: 18px; color: #333; padding: 10px; border-bottom: 2px solid #ddd;")
            self.grid_layout.addWidget(header_name, 0, col)
            col += 1
            # 预设表头（动态获取字段）
            # 为了获取字段，我们需要先创建一个临时的基金对象
            temp_fund = None
            try:
                temp_cfg = configs[0]
                # 生成缓存键
                cache_key = f"temp_{temp_cfg['code']}_{temp_cfg.get('estimate_info', {}).get('code', '')}"
                current_time = datetime.now()
                
                # 如果是强制刷新模式，跳过缓存直接创建新对象
                if hasattr(self, 'force_refresh') and self.force_refresh:
                    temp_fund = self.create_temp_fund(temp_cfg)
                    self.fund_cache[cache_key] = temp_fund
                    self.cache_timestamp[cache_key] = current_time
                # 检查是否有缓存的临时基金对象
                elif (cache_key in self.fund_cache and 
                    cache_key in self.cache_timestamp and
                    (current_time - self.cache_timestamp[cache_key]).total_seconds() < self.cache_timeout):
                    temp_fund = self.fund_cache[cache_key]
                else:
                    temp_fund = self.create_temp_fund(temp_cfg)
                    # 缓存临时基金对象
                    self.fund_cache[cache_key] = temp_fund
                    self.cache_timestamp[cache_key] = current_time
                
                # 获取实际字段并调整顺序
                info_keys = [k for k in temp_fund.info_dict.keys() if k not in ['code', 'name', 'estimate_isupdate', 'estimate_date']]
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
            except Exception as e:
                # 如果无法创建临时基金对象，使用默认字段
                info_keys = [
                    'now_date', 'now_changepercent', 'estimate_changepercent',
                    'now_holtwinters_delta_percentage', 'yesterday_holtwinters_delta_percentage',
                    'factor_fluctuationrateCMA30'
                ]
            for key in info_keys:
                display_text = key
                if key == 'now_date':
                    display_text = '净值日期'
                elif key == 'now_changepercent':
                    display_text = '净值变化'
                elif key == 'estimate_changepercent':
                    display_text = '今日估值'
                elif key == 'now_holtwinters_delta_percentage':
                    display_text = '当前HDP'
                elif key == 'yesterday_holtwinters_delta_percentage':
                    display_text = '昨日HDP'
                elif key == 'factor_holtwinters_estimate_delta_percentage':
                    display_text = '估值HDP'
                elif key == 'factor_fluctuationrateCMA30':
                    display_text = '波动率CMA30'
                header_label = QLabel(display_text)
                header_label.setAlignment(Qt.AlignCenter)
                header_label.setStyleSheet("font-weight: bold; font-family: Futura; font-size: 18px; color: #333; padding: 10px; border-bottom: 2px solid #ddd;")
                header_label.setWordWrap(True)
                self.grid_layout.addWidget(header_label, 0, col)
                col += 1
            # 填充行
            for row_idx, cfg in enumerate(configs, 1):
                row_widgets = []
                # 名称+代码
                name_code_widget = QWidget()
                name_code_widget.setStyleSheet("background-color: white; padding: 8px;")
                name_code_layout = QVBoxLayout(name_code_widget)
                name_code_layout.setContentsMargins(5, 3, 5, 3)
                name_code_layout.setSpacing(2)
                name_label = QLabel(cfg['name'])
                name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                name_label.setStyleSheet("font-family: Futura; font-size: 18px; font-weight: bold; background-color: transparent; margin: 0; padding: 2px 0;")
                name_code_layout.addWidget(name_label)
                code_label = QLabel(cfg['code'])
                code_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                code_label.setStyleSheet("font-family: Futura; font-size: 15px; color: gray; background-color: transparent; margin: 0; padding: 2px 0;")
                name_code_layout.addWidget(code_label)
                self.grid_layout.addWidget(name_code_widget, row_idx, 0)
                row_widgets.append(name_code_widget)
                # 其余列先填Loading...
                for col_idx in range(1, len(info_keys)+1):
                    val_label = QLabel("Loading...")
                    val_label.setAlignment(Qt.AlignCenter)
                    val_label.setStyleSheet("font-family: Futura; font-size: 18px; color: #888; background-color: white; padding: 8px;")
                    self.grid_layout.addWidget(val_label, row_idx, col_idx)
                    row_widgets.append(val_label)
                self.fund_rows.append(row_widgets)

    def on_fund_detail_ready(self, idx, fund):
        # 某只基金加载完，刷新对应行
        if fund is None:
            # 加载失败
            for w in self.fund_rows[idx][1:]:
                w.setText("加载失败")
                w.setStyleSheet("font-family: Futura; font-size: 18px; color: red; background-color: white; padding: 8px;")
            return
        # 获取实际字段并调整顺序（与表头保持一致）
        info_keys = [k for k in fund.info_dict.keys() if k not in ['code', 'name', 'estimate_isupdate', 'estimate_date']]
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
                idx_hdp = info_keys.index('now_holtwinters_delta_percentage')
                info_keys.insert(idx_hdp+1, 'yesterday_holtwinters_delta_percentage')
            else:
                info_keys.append('yesterday_holtwinters_delta_percentage')
        for i, key in enumerate(info_keys):
            val = fund.info_dict.get(key, "")
            label = self.fund_rows[idx][i+1]
            # 格式化显示
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
            
            label.setText(val_str)
            
            # 涨跌幅颜色
            if key in ['estimate_changepercent', 'now_changepercent'] and isinstance(val, float):
                if val > 0:
                    label.setStyleSheet("font-family: Futura; font-size: 18px; color: red; font-weight: bold; background-color: white; padding: 8px;")
                elif val < 0:
                    label.setStyleSheet("font-family: Futura; font-size: 18px; color: green; font-weight: bold; background-color: white; padding: 8px;")
                else:
                    label.setStyleSheet("font-family: Futura; font-size: 18px; background-color: white; padding: 8px;")
            else:
                label.setStyleSheet("font-family: Futura; font-size: 18px; background-color: white; padding: 8px;")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用级别的Futura字体
    font = QFont("Futura", 18)  # 将字体大小设置为18
    app.setFont(font)
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())