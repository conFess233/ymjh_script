# core/themes.py

LIGHT_THEME = {
    "window_bg":         "#f0f0f0",      # 主窗口背景 (Window)
    "text":              "#000000",      # 主文本色 (WindowText / Text)
    "base":              "#ffffff",      # 输入框/内容区域背景 (Base)
    "alternate_base":    "#f7f7f7",      # 按钮背景/隔行背景 (AlternateBase)
    "button":            "#e0e0e0",      # 按钮默认背景 (Button)
    "highlight":         "#0078D7",      # 高亮/选中色 (Highlight)
    "highlighted_text":  "#ffffff",      # 高亮文本色 (HighlightedText)
    "link":              "#2980b9",      # 链接色 (Link)
    "tooltip_base":      "#ffffdc",      # 提示框背景
    "tooltip_text":      "#000000",      # 提示框文本
    "disabled_text":     "#808080",      # 禁用文本色
    "surface":           "#ffffff",      # 卡片/面板背景 (与 base 相同或相似)
    "text_secondary":    "#666666",      # 次级文本色 (用于提示、描述)
    "primary":           "#005A9C",      # 主要操作色 (比 highlight 略深)
    "on_primary":        "#FFFFFF",      # 主要操作色上的文字颜色
    "border":            "#cccccc"       # 控件通用边框色
}

DARK_THEME = {
    "window_bg":         "#2b2b2b",
    "text":              "#FFFFFF",
    "base":              "#3c3f41",
    "alternate_base":    "#2b2b2b",
    "button":            "#3c3f41",
    "highlight":         "#367bf5",
    "highlighted_text":  "#FFFFFF",
    "link":              "#64b5ff",
    "tooltip_base":      "#3c3f41",
    "tooltip_text":      "#7a7a7a",
    "disabled_text":     "#7a7a7a",
    "surface":           "#3c3f41",      # 卡片/面板背景 (比 window_bg 稍亮)
    "text_secondary":    "#aaaaaa",      # 次级文本色
    "primary":           "#4EA6E9",      # 主要操作色 (柔和的蓝色)
    "on_primary":        "#FFFFFF",
    "border":            "#454545"       # 控件通用边框色 (比 alternate_base 亮)
}