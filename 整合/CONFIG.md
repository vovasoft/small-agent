# 配置说明

## 环境变量设置

在使用此项目之前，请确保设置以下环境变量：

### DeepSeek API 配置
```bash
export DEEPSEEK_API_KEY="your_deepseek_api_key_here"
```

### 如何获取API密钥
1. 访问 [DeepSeek官网](https://platform.deepseek.com/)
2. 注册账号并获取API密钥
3. 在终端中设置环境变量：
   ```bash
   echo 'export DEEPSEEK_API_KEY="your_actual_key"' >> ~/.zshrc
   source ~/.zshrc
   ```

### 验证配置
运行以下命令验证环境变量是否正确设置：
```bash
echo $DEEPSEEK_API_KEY
```

如果没有输出或输出为空，请重新设置环境变量。
