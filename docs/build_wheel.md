# AKShare 构建 wheel 文件

本文说明如何在当前项目源码目录中构建 `.whl` 安装包。

## 环境要求

建议使用 Python 3.9 及以上版本，并在项目根目录执行命令。

```powershell
cd D:\CodeWork\akshare
python -m pip install --upgrade build
```

## 构建 wheel

执行以下命令：

```powershell
python -m build --wheel
```

构建完成后，wheel 文件会生成在 `dist` 目录中，例如：

```text
dist\akshare-1.18.64+local.1-py3-none-any.whl
```

包版本号来自 `akshare/_version.py` 中的 `__version__` 字段。

## 清理后重新构建

如果需要删除历史构建产物后重新打包，可以执行：

```powershell
Remove-Item -Recurse -Force build, dist, akshare.egg-info
python -m build --wheel
```

## 安装本地 wheel

构建完成后，可以在当前环境中安装生成的 wheel：

```powershell
python -m pip install .\dist\akshare-1.18.64+local.1-py3-none-any.whl
```

如需覆盖已安装版本：

```powershell
python -m pip install --force-reinstall .\dist\akshare-1.18.64+local.1-py3-none-any.whl
```

## 验证安装

安装完成后，可以检查版本和导入是否正常：

```powershell
python -c "import akshare as ak; print(ak.__version__)"
```

## 常见问题

### 未安装 build

如果执行 `python -m build --wheel` 时提示没有 `build` 模块，请先安装：

```powershell
python -m pip install --upgrade build
```

### 旧文件影响构建结果

如果 `dist` 中已有旧版本 wheel，建议先清理 `build`、`dist` 和 `akshare.egg-info` 后重新构建。

### 安装文件名不一致

wheel 文件名会随 `akshare/_version.py` 中的版本号变化。安装时请以 `dist` 目录中实际生成的文件名为准。
