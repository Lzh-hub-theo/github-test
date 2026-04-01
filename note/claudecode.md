### 前置步骤

**下载claude** 
```ssh
code: npm install -g @anthropic-ai/claude-code
```

下载cc switch来配置claude code的模型提供商

> 坑：claude code 未登录

> 原因：.claude.json下面的hasCompletedOnboarding字段为false

> 坑：400 thinking type should be enabled or disabled

> 原因：不明确，关掉推理模式 ALT+T

> 坑：Error writing file

> 原因：不明确

---

# 基本操作

**切换模式** `shift + tab`

* 默认模式：每次创建寻求同意

* 自动模式：不寻求同意

* 计划模式：构思，不改代码

**修改提示词**
> 老版claude不允许ctrl+回车换行，可以用ctrl+g打开vscode。好了再关闭

**把服务放在后台** `ctrl+b`

**项目回滚到以前的历史状态**
> /rewind 或者 esc+esc
不能回滚终端生成的命令

**切换为普通命令行的命令**
> ! + 终端命令

**回到之前的对话**
> /resume 或者 claude -c 

**上下文压缩** `/compact`

**清空所有上下文** `/clear`

***CLAUDE.md* 获取用户记忆(初始化)** `/init`

**打开CLAUDE.md** `/memory`

**工具使用前后运行用户指定的逻辑** `/hook`

**创建skills**
> 在.claude/skills/your-skill-name 中编写SKILL.md。完成之后`/your-skill-name` 后面加上你的需求就能利用skill了
可以用`/skills`查看已有的skills

**创建subAgent** `/agents`

**agentskill和subagent的区别**
* AgentSkill共享主对话上下文，适合处理跟上下文关联大的内容
* subAgent拥有独立主对话的上下文，适合做与上下文关联小但对上下文影响小的任务

**获得集成 AgentSkills、subAgent、hook 集成功能的工具** `/plugin`