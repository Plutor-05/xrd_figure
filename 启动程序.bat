@echo off
chcp 65001 >nul
title XRD峰匹配分析程序 v3.0

echo ================================
echo XRD峰匹配分析程序 v3.0
echo ================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python环境！
    echo 请先安装Python 3.7或更高版本
    echo.
    pause
    exit /b 1
)

echo Python环境检查通过！
echo.

echo 正在检查依赖包...
python -c "import pandas, matplotlib, scipy, numpy; print('所有依赖包已安装')" 2>nul
if errorlevel 1 (
    echo 正在安装依赖包...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 依赖包安装失败！请手动运行：pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo 依赖包检查通过！
echo.

echo 正在启动程序...
echo.
python start_xrd_analyzer.py

if errorlevel 1 (
    echo.
    echo 程序运行出现错误！
    echo 请检查错误信息或查看用户手册
    pause
)
