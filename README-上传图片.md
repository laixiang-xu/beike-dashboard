# 📷 范画图片上传指南

## 🎯 快速开始（3步）

### 步骤1：准备图片
把范画图片重命名为：`{教师名}_{课程名}.jpg`

**示例：**
```
爱神_热观世界.jpg
西柠_窗边风景.jpg
童言_谁的新衣.jpg
```

### 步骤2：复制到images目录
```
C:\Users\xulaixiang\WorkBuddy\2026-06-15-16-40-32\deploy\images\
```

### 步骤3：双击运行
**双击 `上传图片.bat` 文件** → 自动上传到GitHub

---

## 📋 文件说明

### ✅ 上传图片.bat（推荐）
- **用途：** 上传范画图片到GitHub
- **使用：** 直接双击运行
- **特点：** 无需任何设置，Windows自带支持

### ⚠️ upload-images.ps1（不推荐直接使用）
- **用途：** 同上（PowerShell脚本）
- **问题：** 双击会用记事本打开，不会执行
- **原因：** Windows安全限制
- **如何运行：** 见下方"高级方法"

---

## 🤔 为什么要用.bat而不是.ps1？

### Windows文件类型对比

| 文件类型 | 双击行为 | 说明 |
|---------|---------|------|
| `.bat` | ✅ 直接执行 | Windows批处理文件，可直接运行 |
| `.ps1` | ❌ 记事本打开 | PowerShell脚本，需要特殊方式运行 |
| `.cmd` | ✅ 直接执行 | 同.bat，旧版批处理 |
| `.vbs` | ✅ 直接执行 | VBScript脚本 |

**结论：** 用`.bat`最简单，双击即可运行。

---

## 🔧 高级方法（如果你想用.ps1）

### 方法1：右键菜单
1. 右键点击 `upload-images.ps1`
2. 选择 **"使用 PowerShell 运行"**

### 方法2：PowerShell窗口
```powershell
cd C:\Users\xulaixiang\WorkBuddy\2026-06-15-16-40-32\deploy
.\upload-images.ps1
```

### 方法3：解除PowerShell执行限制（一劳永逸）

**如果右键没有"使用PowerShell运行"选项，或者运行时报错"无法加载"：**

1. 按 `Win + X`，选择 **"Windows PowerShell (管理员)"**
2. 输入：
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. 提示时输入 `Y` 回车

之后所有`.ps1`文件都可以右键运行了。

---

## 📊 完整工作流程

### 每周操作流程

```
周一上午：
├─ 1. 从飞书导出Excel
├─ 2. 收集范画图片
├─ 3. 图片重命名：{教师名}_{课程名}.jpg
└─ 4. 发给AI评分（等待30分钟）

周一下午：
├─ 5. 收到增强版Excel（含AI评分）
├─ 6. 把范画图片复制到 images/ 目录
├─ 7. 双击 "上传图片.bat"
├─ 8. 等待1-2分钟
├─ 9. 打开dashboard上传Excel
└─ 10. 发送链接给业务部门
```

**总耗时：你的操作 < 10分钟**

---

## 🆘 常见问题

### Q1: 双击.bat后一闪而过？
**原因：** Git命令执行太快，窗口自动关闭
**解决：** 这是正常的！说明上传成功了

如果想看详细过程，打开.bat文件，最后有`pause`命令会暂停。

### Q2: 双击.bat报错"git不是内部命令"？
**原因：** Git未安装或未添加到环境变量
**解决：** 
```powershell
# 测试Git是否安装
git --version

# 如果显示版本号，说明已安装
# 如果报错，需要安装Git：https://git-scm.com/download/win
```

### Q3: 双击.bat后提示"权限不足"？
**原因：** 文件夹权限问题
**解决：** 右键.bat文件 → 以管理员身份运行

### Q4: 图片上传后dashboard还是看不到？
**可能原因：**
1. GitHub Pages部署延迟（等2-3分钟）
2. 浏览器缓存（按Ctrl+F5刷新）
3. 图片命名不匹配（检查命名格式）

**排查方法：**
- 访问：https://github.com/laixiang-xu/beike-dashboard/tree/main/images
- 确认图片已经上传
- 对比文件名和Excel中的老师名、课程名

### Q5: 想撤销刚才的上传？
```powershell
cd C:\Users\xulaixiang\WorkBuddy\2026-06-15-16-40-32\deploy

# 撤销最后一次提交（保留图片文件）
git reset --soft HEAD~1

# 或者删除某个图片后重新提交
git rm images/某个图片.jpg
git commit -m "删除错误图片"
git push origin main -f
```

---

## 📖 扩展知识

### .bat vs .ps1 的区别

**批处理文件 (.bat / .cmd)**
- ✅ 双击即可运行
- ✅ 兼容所有Windows版本
- ✅ 语法简单
- ❌ 功能较弱

**PowerShell脚本 (.ps1)**
- ❌ 不能直接双击运行
- ✅ 功能强大（对象、管道、.NET）
- ✅ 跨平台（PowerShell Core）
- ⚠️ 需要执行策略设置

### 为什么Windows限制.ps1双击运行？

**安全考虑：**
- PowerShell功能强大，可以执行任何系统操作
- 恶意脚本可能伪装成普通文件
- 防止用户误点恶意脚本

**对比：**
- `.bat`历史悠久，功能受限，风险较小
- `.ps1`现代强大，需要用户主动确认运行

---

## 🎓 学习资源

### 如果你想深入学习：

**批处理 (.bat)**
- 教程：https://www.tutorialspoint.com/batch_script/
- 适合：快速自动化简单任务

**PowerShell (.ps1)**
- 官方文档：https://docs.microsoft.com/powershell/
- 适合：复杂系统管理任务

**Git命令**
- 入门：https://git-scm.com/book/zh/v2
- 适合：版本控制和协作

---

## ✅ 总结

**你只需要记住：**

1. **双击 `上传图片.bat`** = 上传图片到GitHub
2. **.bat文件可以直接双击运行**
3. **.ps1文件需要右键选择"使用PowerShell运行"**

**就这么简单！** 🎉

---

*有问题随时查看这个文档，或者问AI助手*
