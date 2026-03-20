"""
Batch translate Chinese labels in OpenMAIC config files.
Uses a deterministic mapping dictionary for standard UI terms.
"""

import re
import os

# Deterministic Chinese → English mappings for config labels
TRANSLATIONS = {
    # Symbol categories (configs/symbol.ts)
    '字母': 'Letters',
    '序号': 'Numbering',
    '数学': 'Math',
    '箭头': 'Arrows',
    '图形': 'Shapes',

    # Shape types (configs/shapes.ts)
    '矩形': 'Rectangle',
    '常用形状': 'Common Shapes',
    '其他形状': 'Other Shapes',
    '线性': 'Linear',

    # Lines (configs/lines.ts)
    '直线': 'Straight Lines',
    '折线、曲线': 'Polylines & Curves',

    # LaTeX formulas (configs/latex.ts)
    '高斯公式': 'Gaussian Formula',
    '傅里叶级数': 'Fourier Series',
    '泰勒展开式': 'Taylor Expansion',
    '定积分': 'Definite Integral',
    '三角恒等式1': 'Trig Identity 1',
    '三角恒等式2': 'Trig Identity 2',
    '和的展开式': 'Binomial Expansion',
    '欧拉公式': "Euler's Formula",
    '贝努利方程': 'Bernoulli Equation',
    '全微分方程': 'Exact Differential Equation',
    '非齐次方程': 'Non-homogeneous Equation',
    '柯西中值定理': "Cauchy's Mean Value Theorem",
    '拉格朗日中值定理': "Lagrange's Mean Value Theorem",
    '导数公式': 'Derivative Formula',
    '三角函数积分': 'Trigonometric Integral',
    '二次曲面': 'Quadric Surface',
    '二阶微分': 'Second-order Differential',
    '方向导数': 'Directional Derivative',
    '组合': 'Combinatorics',
    '函数': 'Functions',
    '希腊字母': 'Greek Letters',

    # Image clip shapes (configs/image-clip.ts)
    '矩形2': 'Rectangle 2',
    '矩形3': 'Rectangle 3',
    '圆角矩形': 'Rounded Rectangle',
    '圆形': 'Circle',
    '三角形': 'Triangle',
    '三角形2': 'Triangle 2',
    '三角形3': 'Triangle 3',
    '菱形': 'Diamond',
    '五边形': 'Pentagon',
    '六边形': 'Hexagon',
    '七边形': 'Heptagon',
    '八边形': 'Octagon',
    'V形': 'V-shape',
    '点': 'Dot',
    '星形': 'Star',
    '星形2': 'Star 2',
    '十字形': 'Cross',
    '加号': 'Plus',
    '对话框': 'Speech Bubble',
    '对话框2': 'Speech Bubble 2',

    # Hotkeys (configs/hotkey.ts)
    '撤销': 'Undo',
    '重做': 'Redo',
    '剪切': 'Cut',
    '复制': 'Copy',
    '粘贴': 'Paste',
    '全选': 'Select All',
    '删除': 'Delete',
    '保存': 'Save',
    '上移': 'Move Up',
    '下移': 'Move Down',
    '左移': 'Move Left',
    '右移': 'Move Right',
    '放大': 'Zoom In',
    '缩小': 'Zoom Out',
    '加粗': 'Bold',
    '斜体': 'Italic',
    '下划线': 'Underline',
    '居中': 'Center',
    '左对齐': 'Align Left',
    '右对齐': 'Align Right',
    '锁定': 'Lock',
    '解锁': 'Unlock',
    '组合': 'Group',
    '取消组合': 'Ungroup',
    '置于顶层': 'Bring to Front',
    '置于底层': 'Send to Back',
    '上移一层': 'Bring Forward',
    '下移一层': 'Send Backward',

    # Font (configs/font.ts)
    '宋体': 'SimSun',
    '黑体': 'SimHei',
    '楷体': 'KaiTi',
    '仿宋': 'FangSong',
    '微软雅黑': 'Microsoft YaHei',
    '华文细黑': 'STXihei',
    '华文黑体': 'STHeiti',
    '华文楷体': 'STKaiti',
    '华文宋体': 'STSong',
    '华文仿宋': 'STFangsong',
    '等线': 'DengXian',

    # Chart (configs/chart.ts)
    '柱状图': 'Bar Chart',
    '折线图': 'Line Chart',
    '饼图': 'Pie Chart',
    '环形图': 'Doughnut Chart',
    '面积图': 'Area Chart',
    '散点图': 'Scatter Chart',
    '雷达图': 'Radar Chart',

    # Animation (configs/animation.ts)
    '淡入': 'Fade In',
    '淡出': 'Fade Out',
    '飞入': 'Fly In',
    '飞出': 'Fly Out',
    '缩放': 'Zoom',
    '旋转': 'Spin',
    '弹跳': 'Bounce',
    '闪烁': 'Flash',
    '擦除': 'Wipe',
    '滑入': 'Slide In',
    '滑出': 'Slide Out',
    '浮入': 'Float In',
    '浮出': 'Float Out',
    '翻转': 'Flip',
    '展开': 'Expand',
    '进入': 'Enter',
    '退出': 'Exit',
    '强调': 'Emphasis',
    '切换': 'Switch',
    '无': 'None',
    '随机': 'Random',
    '向左': 'Left',
    '向右': 'Right',
    '向上': 'Up',
    '向下': 'Down',
    '从左': 'From Left',
    '从右': 'From Right',
    '从上': 'From Top',
    '从下': 'From Bottom',
    '从左上': 'From Top-Left',
    '从右上': 'From Top-Right',
    '从左下': 'From Bottom-Left',
    '从右下': 'From Bottom-Right',
    '中心': 'Center',
    '水平': 'Horizontal',
    '垂直': 'Vertical',

    # Element (configs/element.ts)
    '文本': 'Text',
    '图片': 'Image',
    '形状': 'Shape',
    '线条': 'Line',
    '图表': 'Chart',
    '表格': 'Table',
    '公式': 'Formula',
    '视频': 'Video',
    '音频': 'Audio',

    # Generic
    '默认': 'Default',
    '自定义': 'Custom',
    '其他': 'Other',
    '基础': 'Basic',
    '高级': 'Advanced',
    '名称': 'Name',
    '描述': 'Description',
    '标题': 'Title',
    '内容': 'Content',
    '类型': 'Type',
    '大小': 'Size',
    '颜色': 'Color',
    '位置': 'Position',
    '宽度': 'Width',
    '高度': 'Height',
    '透明度': 'Opacity',
    '边框': 'Border',
    '圆角': 'Rounded',
    '阴影': 'Shadow',
    '旋转': 'Rotation',
    '翻转': 'Flip',
    '对齐': 'Align',
    '分布': 'Distribute',
    '排列': 'Arrange',
}

CONFIG_DIR = r"n:\projects\govware\OpenMAIC\configs"

def translate_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    changes = 0

    # Sort by length descending to match longer phrases first
    for zh, en in sorted(TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        # Match Chinese text within quotes (single or double)
        for quote in ["'", '"']:
            pattern = f"{quote}{re.escape(zh)}{quote}"
            replacement = f"{quote}{en}{quote}"
            if pattern in content:
                content = content.replace(pattern, replacement)
                changes += 1

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ {os.path.basename(filepath)}: {changes} translations applied")
    else:
        print(f"  - {os.path.basename(filepath)}: no changes needed")

    return changes


def main():
    total = 0
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith('.ts'):
            filepath = os.path.join(CONFIG_DIR, filename)
            total += translate_file(filepath)

    print(f"\nTotal: {total} translations applied across config files")


if __name__ == "__main__":
    main()
