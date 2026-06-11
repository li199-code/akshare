# Fork 同步说明

本仓库是从上游仓库 fork 而来，默认维护方式如下：

- `origin`: 自己的 fork 仓库
- `upstream`: 原始仓库 `https://github.com/akfamily/akshare.git`

## 当前约定

本地 `main` 分支跟踪 `origin/main`，默认推送远程也设置为 `origin`。

这样做的目的是避免在 `main` 上执行 `git push` 时误推到 `upstream`。

## 同步上游 main

执行下面的命令，将上游仓库的 `main` 合并到本地 `main`，并推送到自己的 fork：

```bash
git switch main
git fetch upstream
git merge upstream/main
git push origin main
```

也可以直接使用本地配置好的 git alias：

```bash
git sync-upstream
```

该 alias 等价于：

```bash
git switch main && git fetch upstream && git merge upstream/main && git push origin main
```

## 冲突处理

如果执行 `git merge upstream/main` 时发生冲突，按正常 Git 流程处理：

```bash
git status
```

解决冲突后执行：

```bash
git add .
git commit
git push origin main
```

## 检查远程配置

如需确认远程配置是否正确，可执行：

```bash
git remote -v
git branch -vv
```

期望结果：

- `origin` 指向自己的 fork
- `upstream` 指向 `https://github.com/akfamily/akshare.git`
- 本地 `main` 跟踪 `origin/main`
