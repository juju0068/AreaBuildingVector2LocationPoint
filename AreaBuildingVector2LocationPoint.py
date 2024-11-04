"""
Class:GIS Software Engineering
Author:juju0068
代码已使用如flake8等格式矫正器进行格式化
"""

import os
import sys

import geopandas as gpd
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QMainWindow,
                             QToolBar, QVBoxLayout, QWidget)


def open_basemap(win):
    """打开底图文件，并设置为基础图层。

    参数:
    - win: 主窗口对象，用于访问主窗口的属性和方法。

    此函数通过文件对话框加载Shapefile格式的底图文件，并将其显示在主窗口的画布上。
    同时，它还会保存底图的边界信息，以便于后续操作。
    """
    file_path, _ = QFileDialog.getOpenFileName(
        None, "选择底图文件", "", "Shapefiles (*.shp)"
    )
    if file_path:
        try:
            basemap = gpd.read_file(file_path)
            win.basemap = basemap  # 保存底图
            win.statusBar().showMessage(f"底图已加载: {file_path}")
            display_basemap(basemap, win.canvas)

            # 获取并保存底图的边界信息
            x_min, y_min, x_max, y_max = basemap.total_bounds
            win.basemap_xlim = (x_min, x_max)
            win.basemap_ylim = (y_min, y_max)

            # 启用“打开建筑文件”按钮
            win.open_file_action.setEnabled(True)
        except Exception as e:
            win.statusBar().showMessage(f"无法加载底图: {e}")


def display_basemap(basemap, canvas):
    """显示底图在画布上。

    参数:
    - basemap: GeoDataFrame对象，表示底图数据。
    - canvas: FigureCanvas对象，用于绘制底图。

    此函数负责将给定的底图数据绘制到指定的画布上，作为基础图层。
    它首先清除画布上的现有图形，然后绘制底图。
    """
    canvas.axes.clear()
    basemap.plot(
        ax=canvas.axes, color="lightgrey", edgecolor="black", alpha=0.5
    )
    canvas.draw()


def open_shp_file(win):
    """
    打开GIS文件，自动转换坐标系并显示在底图之上。

    参数:
    - win: 主窗口对象，应包含basemap属性和statusBar方法。

    返回值:
    无
    """
    # 检查是否已加载底图
    if not hasattr(win, "basemap"):
        win.statusBar().showMessage("请先加载底图！")
        return

    # 弹出文件对话框，让用户选择Shapefile文件
    file_path, _ = QFileDialog.getOpenFileName(
        None, "选择文件", "", "Shapefiles (*.shp)"
    )
    if file_path:
        # 验证文件类型
        if not file_path.endswith(".shp"):
            win.statusBar().showMessage("文件类型错误，请选择 Shapefile 文件")
            return

        try:
            # 读取GIS数据
            gdf = gpd.read_file(file_path)
            # 如果坐标系不匹配，则转换坐标系
            if gdf.crs != win.basemap.crs:
                gdf = gdf.to_crs(win.basemap.crs)
            win.gdf = gdf  # 保存GeoDataFrame到窗口对象
            win.statusBar().showMessage(f"文件已打开: {file_path}")

            # 显示建筑物及其位置点
            display_and_save_shp_data(gdf, win.canvas, win, file_path)
        except Exception as e:
            win.statusBar().showMessage(f"无法打开文件: {e}")


def display_and_save_shp_data(gdf, canvas, win, file_path):
    """
    显示并保存GIS数据，确保在底图的比例和范围内叠加显示。

    参数:
    - gdf: GeoDataFrame对象，包含GIS数据。
    - canvas: 用于绘制的画布对象。
    - win: 主窗口对象，用于访问basemap和其他属性。
    - file_path: 文件路径，用于保存位置点数据。

    返回值:
    无
    """
    # 验证输入数据类型
    if not isinstance(gdf, gpd.GeoDataFrame):
        print("输入数据必须是 GeoDataFrame 类型")
        return

    # 绘制底图并绘制GIS数据
    display_basemap(win.basemap, canvas)
    gdf.plot(ax=canvas.axes, color="blue", edgecolor="black", alpha=0.5)

    # 计算并绘制位置点
    position_points = gdf.geometry.centroid
    position_points.plot(ax=canvas.axes, color="red", markersize=10)

    # 设置画布的范围，确保与底图一致
    canvas.axes.set_xlim(win.basemap_xlim)
    canvas.axes.set_ylim(win.basemap_ylim)

    canvas.draw()

    # 保存位置点为新的shp文件
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.join(
        os.path.dirname(file_path), "zhuhai_bnu_all_point"
    )

    # 创建输出目录，如果它不存在的话
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    default_file_name = f"{base_name}_point.shp"
    position_file_path, _ = QFileDialog.getSaveFileName(
        None,
        "保存位置点文件",
        os.path.join(output_dir, default_file_name),
        "Shapefiles (*.shp)",
    )

    if position_file_path:
        position_points_df = gpd.GeoDataFrame(
            geometry=position_points, crs=gdf.crs
        )
        position_points_df.to_file(position_file_path)
        win.statusBar().showMessage(f"位置点已保存为 '{position_file_path}'")
        print(f"位置点已保存为 '{position_file_path}'")
    else:
        win.statusBar().showMessage("保存操作已取消")


class MainWindow(QMainWindow):
    """
    校园建筑物矢量图查看器的主窗口类，支持底图导入和建筑物矢量图层叠加。
    """

    def __init__(self):
        """
        初始化主窗口。
        """
        super().__init__()
        self.gdf = None  # 用于存储建筑 GeoDataFrame
        self.basemap = None  # 用于存储底图
        self.basemap_xlim = None
        self.basemap_ylim = None
        self.init_ui()

    def init_ui(self):
        """
        初始化用户界面。
        创建工具栏、状态栏、绘图区域和主布局，并设置窗口标题。
        """
        # 创建工具栏
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)

        # 底图加载和清除操作
        load_basemap_act = QAction("加载底图", self)
        load_basemap_act.triggered.connect(lambda: open_basemap(self))
        toolbar.addAction(load_basemap_act)

        clear_basemap_act = QAction("清除底图", self)
        clear_basemap_act.triggered.connect(self.clear_basemap)
        toolbar.addAction(clear_basemap_act)

        # 创建打开文件动作，并禁用初始状态
        self.open_file_action = QAction("打开建筑文件", self)
        self.open_file_action.setEnabled(False)  # 初始禁用
        self.open_file_action.triggered.connect(lambda: open_shp_file(self))
        toolbar.addAction(self.open_file_action)

        # 设置状态栏
        self.statusBar().showMessage("准备就绪")

        # 创建绘图区域
        self.canvas = MplCanvas(self, width=8, height=6, dpi=100)

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.canvas)

        # 创建中心部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.setWindowTitle("建筑物矢量图查看器")

    def clear_basemap(self):
        """
        清除底图，允许重新加载。
        这个函数重置底图属性，并清除绘图区域中的内容。
        """
        self.basemap = None
        self.basemap_xlim = None
        self.basemap_ylim = None
        self.canvas.axes.clear()
        self.statusBar().showMessage("底图已清除")
        self.canvas.draw()

        # 禁用“打开建筑文件”按钮
        self.open_file_action.setEnabled(False)



class MplCanvas(FigureCanvas):
    """
    Matplotlib画布组件。
    这个类创建了一个绘图区域，用于显示图形。
    """

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """
        初始化画布组件。
        创建一个Figure对象，并添加一个子图，隐藏坐标轴。
        """
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.axis("off")  # 隐藏坐标轴
        super(MplCanvas, self).__init__(fig)


# 主程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
