

##功能说明
### 使用mcp的Python-sdk编写的mcp服务，使用大模型调用glances的api并将返回结果交由大模型分析展示，客户端测试过cursor和cline的mcp服务

## 配置说明
在需要监控的服务上安装glances，并且启动webUI，放开61208端口
本地需要安装uv，https://hellowac.github.io/uv-zh-cn/guides/integration/pytorch/
根据mcp官网文档初始化项目，https://modelcontextprotocol.io/quickstart/server，将man.py替换为项目Python文件
###cline客户端mcp服务配置
{
  "mcpServers": {
      "mcp-test": {
          "command": "uv",
          "args": [
              "--directory",
              "E:\\code\\mcp-test\\",
              "run",
              "glances_info_mcp.py"
          ],
        "disable":false,
        "autoApprove":[]
      }
  }
}
###cursor客户端mcp服务配置
{
  "mcpServers": {
      "mcp-test": {
          "command": "uv",
          "args": [
              "--directory",
              "E:\\code\\mcp-test\\",
              "run",
              "glances_info_mcp.py"
          ]
      }
  }
}
使用cline客户端需要将vscode已管理员身份运行，cursor不需要,添加配置后需要重启vscode并且新建会话

### 服务器配置

在`servers_configs.json`中，配置监控的服务器：

{
    "server1": {
        "name": "测试服务器",
        "url": "http://127.0.0.1:61208/api/4",
        "description": "测试环境主服务器"
    },
    "server2": {
        "name": "生产服务器",
        "url": "http://192.168.0.1:61208/api/4",
        "description": "生产环境主服务器"
    }
}



## 错误处理

系统会自动处理常见错误情况：

- 服务器不存在
- 网络连接失败
- API调用超时
- 数据格式错误

所有错误都会返回友好的错误信息，便于问题诊断。

## 注意事项

1. 确保目标服务器的Glances Web服务器已正确启动
2. 检查网络连接和防火墙设置
3. 定期检查和更新服务器配置
4. 建议设置合适的超时时间

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。在提交代码前，请确保：

1. 代码符合Python代码规范
2. 添加了必要的注释和文档
3. 通过了所有测试用例

## 许可证

[添加许可证信息]
