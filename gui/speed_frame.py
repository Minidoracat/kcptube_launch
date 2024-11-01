import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from .base_frame import BaseFrame
from logger import logger

class SpeedFrame(BaseFrame):
    """速度設定頁面"""
    def __init__(self, master, speedtest_manager, **kwargs):
        self.speedtest = speedtest_manager
        super().__init__(master, padding=15, **kwargs)
    
    def init_ui(self):
        """初始化速度設定頁面"""
        # 速度輸入區域
        speed_input_frame = ttk.Frame(self)
        speed_input_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            speed_input_frame,
            text="下載速度 (M):",
            style='info'
        ).pack(side=LEFT, padx=(0, 5))
        
        self.download_speed_var = tk.StringVar()
        self.download_speed_entry = ttk.Entry(
            speed_input_frame,
            textvariable=self.download_speed_var,
            width=10,
            font=('微軟正黑體', 10)
        )
        self.download_speed_entry.pack(side=LEFT, padx=(0, 20))
        
        ttk.Label(
            speed_input_frame,
            text="上傳速度 (M):",
            style='info'
        ).pack(side=LEFT, padx=(0, 5))
        
        self.upload_speed_var = tk.StringVar()
        self.upload_speed_entry = ttk.Entry(
            speed_input_frame,
            textvariable=self.upload_speed_var,
            width=10,
            font=('微軟正黑體', 10)
        )
        self.upload_speed_entry.pack(side=LEFT)
        
        # 自動套用選項
        self.auto_apply_var = tk.BooleanVar()
        self.auto_apply_checkbox = ttk.Checkbutton(
            self,
            text="自動套用速度設定到節點",
            variable=self.auto_apply_var,
            command=self.on_auto_apply_changed,
            style='round-toggle'
        )
        self.auto_apply_checkbox.pack(fill=X, pady=10)
        
        # 速度控制按鈕
        speed_control_frame = ttk.Frame(self)
        speed_control_frame.pack(fill=X)
        
        self.apply_speed_button = ttk.Button(
            speed_control_frame,
            text="套用設定到節點",
            command=self.apply_speed_settings,
            style='primary-outline',
            width=15
        )
        self.apply_speed_button.pack(side=LEFT, padx=(0, 10))
        
        self.speedtest_button = ttk.Button(
            speed_control_frame,
            text="測試網路速度",
            command=self.start_speedtest,
            style='info-outline',
            width=15
        )
        self.speedtest_button.pack(side=LEFT)
        
        self.speed_info_label = ttk.Label(
            speed_control_frame,
            text="目前未設定速度",
            style='info'
        )
        self.speed_info_label.pack(side=RIGHT)
        
        # 載入速度設定
        self.load_speed_settings()
    
    def load_speed_settings(self):
        """載入速度設定"""
        speeds = self.speedtest.get_current_speeds()
        self.download_speed_var.set(str(int(speeds['download_speed'])))
        self.upload_speed_var.set(str(int(speeds['upload_speed'])))
        self.auto_apply_var.set(speeds['auto_apply'])
        
        # 根據自動套用設定更新按鈕狀態
        if speeds['auto_apply']:
            self.apply_speed_button['state'] = 'disabled'
        else:
            self.apply_speed_button['state'] = 'normal'
        
        self.update_speed_info()
    
    def update_speed_info(self):
        """更新速度資訊顯示"""
        speeds = self.speedtest.get_current_speeds()
        mode = "手動設定" if speeds['manual_mode'] else "自動測試"
        last_test = speeds.get('last_test', '從未測試')
        auto_apply = "自動套用已啟用" if speeds['auto_apply'] else "自動套用已停用"
        self.speed_info_label['text'] = (
            f"目前速度設定 ({mode}):\n"
            f"下載: {int(speeds['download_speed'])}M | "
            f"上傳: {int(speeds['upload_speed'])}M\n"
            f"最後更新: {last_test}\n"
            f"{auto_apply}"
        )
    
    def on_auto_apply_changed(self):
        """當自動套用勾選框狀態改變時"""
        enabled = self.auto_apply_var.get()
        self.speedtest.set_auto_apply(enabled)
        if enabled:
            self.apply_speed_button['state'] = 'disabled'
            logger.info("已啟用自動套用速度設定到節點")
        else:
            self.apply_speed_button['state'] = 'normal'
            logger.info("已停用自動套用速度設定到節點")
    
    def apply_speed_settings(self):
        """套用速度設定"""
        try:
            download = float(self.download_speed_var.get())
            upload = float(self.upload_speed_var.get())
            
            if download <= 0 or upload <= 0:
                raise ValueError("速度必須大於 0")
            
            self.speedtest.set_manual_speeds(download, upload)
            self.update_speed_info()
            
            # 更新設定檔
            if self.speedtest.update_conf_files():
                messagebox.showinfo('成功', '速度設定已更新')
                # 發送更新事件
                self.event_generate('<<SpeedSettingsUpdated>>')
            else:
                messagebox.showwarning('警告', '速度設定已儲存，但更新設定檔時發生錯誤')
        except ValueError as e:
            messagebox.showerror('錯誤', '請輸入有效的數字')
    
    def start_speedtest(self):
        """開始速度測試"""
        if self.speedtest.is_running():
            logger.warning("速度測試已在進行中")
            return
        
        def on_test_complete(result):
            """速度測試完成的回調函數"""
            self.download_speed_var.set(str(int(result['download_speed'])))
            self.upload_speed_var.set(str(int(result['upload_speed'])))
            self.update_speed_info()
            
            # 如果啟用了自動套用，則更新設定檔
            if self.auto_apply_var.get():
                if self.speedtest.update_conf_files():
                    messagebox.showinfo('成功', '速度測試完成並已更新設定')
                    # 發送更新事件
                    self.event_generate('<<SpeedSettingsUpdated>>')
                else:
                    messagebox.showwarning('警告', '速度測試完成，但更新設定檔時發生錯誤')
            else:
                messagebox.showinfo('成功', '速度測試完成')
            
            self.speedtest_button['text'] = '測試網路速度'
            self.speedtest_button['state'] = 'normal'
        
        self.speedtest_button['text'] = '測試中...'
        self.speedtest_button['state'] = 'disabled'
        self.speed_info_label['text'] = '正在進行速度測試，請稍候...'
        
        self.speedtest.start_test(on_test_complete)
