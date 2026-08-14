# Ilina 的本体应该：
1. 提供 API Call 能力
2. 加载插件（工作区/全局）
3. 管理记忆和日志
4. 提供标签页/窗口管理

# Ilina 的插件可以：
1. 实现一个具体的功能（树状对话、待办列表、做题反馈……）
2. 提供 MCP、Skill
3. 提供一个窗口（标签页）用来交互
4. 告诉本体”我产出了什么记忆“和”你可以如何读取我产出的记忆“

# Ilina WorkSpace
这是本体。
## API Call
### 它提供什么？
它提供一个调用能力，可以是 OpenAI 协议、Ollama、llama.cpp 或者是别的什么。
然后把一切都都封装成[[IlinaMessage]]来传递
### 接口
`invoke`：传入一个消息列表，调用并流式返回结果。会自动处理记忆和工具调用。
`singleShot`：传入一个消息列表，调用并返回结果。不会添加任何处理，就是完全的转发。

> [!QUESTON] 应该如何流式传递？
> 目前的 Node Event 设计是专门为树状对话准备的，但我想让它更加通用

## 加载插件
扫描安装目录插件文件夹和工作区的插件文件夹，然后根据配置文件跳过禁用的插件，最后加载所有插件
#### 暴露的接口
`create_window`：创建 GUI
`get_tool`：获取[[IlinaMessage#3. `IlinaToolDefinition` — MCP 工具定义|IlinaToolDefinition]]的列表
`get_skills`：获取一个类似的，skill def 的列表
`get_system_replace`：会添加到系统提示的记忆
通过工具暴露记忆目录和具体查询

# 遗憾
很抱歉，但……Deepseek harness，那其实就是我梦想中的 Ilina 应该有的样子。Ilina GUI 的开发会暂缓一段时间……