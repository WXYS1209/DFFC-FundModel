# ============================================================
# 作者: Rick Xie
# 日期: 2025/05/14
# 邮箱: xie_jinxiao@126.com
# 文件用途: 基金监控程序
# 其他信息: 
# ============================================================

import maliang
from matplotlib.figure import Figure
from maliang import mpl, theme, animation, theme, toolbox
from maliang.core import configs, virtual

# 导入字体
if toolbox.load_font("./fonts/LXGWWenKai-Regular.ttf"):
    configs.Font.family = "LXGW WenKai"

#=======================================================

# 0. 设置主窗口
main_x = 1920
main_y = 1080
root = maliang.Tk(size= (main_x,main_y),title="Fund Monitor")
root.center()

# 1. 创建主画布
cv = maliang.Canvas(auto_zoom=True, keep_ratio="min", free_anchor=True, auto_update=False, bg="white",highlightbackground="white", highlightcolor="white")
cv.place(width=main_x, height=main_y, x=main_x/2, y=main_y/2, anchor="center")

# 在左上角添加标题
cv.create_text(30, 30, text="Fund Information", anchor="nw", font=("LXGW WenKai", 32, "bold"), fill="#222222")

# 2. 创建图表


# 运行主循环
root.mainloop()