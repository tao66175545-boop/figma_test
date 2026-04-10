# AI友好的设计系统规范

这是一套为AI工具（Claude、Codex、Cursor等）优化的设计系统规范模板。

## 项目结构

```
design-system/
├── index.json              # 设计系统索引文件
├── tokens/                 # 设计令牌
│   ├── colors.json         # 颜色令牌
│   ├── typography.json     # 字体令牌
│   ├── spacing.json        # 间距令牌
│   └── effects.json        # 效果令牌（阴影、圆角等）
└── components/             # 组件规范
    ├── button.json         # 按钮组件
    ├── input.json          # 输入框组件
    └── card.json           # 卡片组件
```

## AI工具使用指南

### 引用设计令牌

在代码中使用设计令牌时，可以参考以下格式：

```javascript
// 颜色
const primaryColor = tokens.colors.primary[500];  // #2196F3

// 间距
const padding = tokens.spacing[4];  // 16px

// 字体
const fontSize = tokens.typography.fontSize.base;  // 16px
```

### 组件规范

每个组件规范包含：
- `variants`: 组件变体（如primary、secondary）
- `sizes`: 组件尺寸（sm、md、lg）
- `states`: 组件状态（default、hover、active、disabled）
- `usage`: 使用指南（do和dont）

## Figma源文件

- 源文件: https://www.figma.com/design/8EPfafesUWZV92e2VqfmRq/
- 目标文件: https://www.figma.com/design/bNbp9f3xwWpNvSTMGahf8r/

## 如何更新设计规范

1. 在Figma中导出设计变量（Variables）为JSON格式
2. 将导出的内容更新到对应的tokens文件中
3. 更新components中的组件规范

## 许可证

MIT