# IlinaGUI
为 Ilina Engine 设计的 GUI 界面。不过你也可以自己写一个 : ) 

# 如何设置工作区配置
首先，在你存放 `.ilinatree` 的文件夹创建一个 `.ilinaconfig` 文件，然后复制以下内容：
```JSON
{
  "workpath": "D:\\Find-A-Way-VII\\IlinaGUI",
  "open_or_alarm": true,
  "ignores": []
}
```
`workpath` 可以指定一个目录，作为 Ilina 的工作目录，默认是 `.ilinatree` 所在的目录。
`open_or_alarm` 可以指定 Ilina 的默认行为，为 true 时默认编辑后打开文件，为 false 时默认编辑后发送通知。
`ingores` 可以指定屏蔽的文件或文件夹，Ilina 无法访问屏蔽的文件或文件夹。

# 如何设置 API 服务商和 MCP 
首先需要打开你本地的 IlinaGUI 的目录，找到 `configs/engine.json`，打开。
```JSON
{
  "main_model": {
    "base_url": "https://api.deepseek.com",
    "api_key": "sk-xxxx",
    "model_name": "deepseek-v4-pro"
  },
  "sub_model": {
    "base_url": "http://localhost:11434/v1/",
    "api_key": "sk-xxx",
    "model_name": "qwen3-vl:4b"
  },
  "mcps": {
    "office-word": {
      "command": "path\\to\\mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "path\\to\\mcp\\main.py"
      ]
    }
  },
  "default_system_prompt_template": "D:\\Find-A-Way-VII\\IlinaGUI\\configs\\default_system.md",
  "global_ignores": [
    ".venv",
    "*.ilinatree",
    ".git",
    ".obsidian"
  ],
  "toast_icon_abs_path": null
}
```
按上例配置 main_model 和 mcp 即可，mcp 的配置就如同在 Claude Code 里一样。
另外，这里的 global_ignores 是全局的屏蔽，作用和工作区屏蔽相同，但对所有工作区默认生效

# 在右键菜单中添加 “在此处新建 Ilina 对话树”
可以参考如下的注册表并手动添加：
```
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\Directory\Background\shell\IlinaGUI]
@="在此处新建Ilina对话树"
"Icon"="path\\to\\IlinaGUI\\images\\ico.ico"

[HKEY_CLASSES_ROOT\Directory\Background\shell\IlinaGUI\command]
@="\"path\\to\\IlinaGUI\\IlinaGUI.exe\" \"%V\""
```


# 更新日志
## v0.8.5
 - 紧急修复了FastMCP的横幅问题 : )

## v0.8.2
 - 增加了对 IlinaEngine 内部工具的支持