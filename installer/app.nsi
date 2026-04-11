; ============================================================
;  河北省高考志愿填报系统 - NSIS 安装脚本
;  需要 NSIS 3.0+ / Unicode 版本
;  编译: makensis app.nsi
; ============================================================

!define APP_NAME "河北省高考志愿填报系统"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "张哥开发部"
!define APP_EXE "河北高考志愿填报系统.exe"
!define COMP_NAME "HebeiGaokaoVolunteer"

; ------------------------------------------------------------
; 安装程序基本信息
; ------------------------------------------------------------
Name "${APP_NAME}"
OutFile "..\installer\${COMP_NAME}_Setup_v${APP_VERSION}.exe"
InstallDir "$LOCALAPPDATA\${APP_NAME}"        ; 用户目录，无需管理员权限
InstallDirRegKey HKLM "Software\${COMP_NAME}" "InstallPath"
RequestExecutionLevel user                     ; 用户权限，不弹UAC提示

; 现代UI界面（Unicode）
!include "MUI2.nsh"

; 安装程序图标
!define MUI_ICON "..\resources\icon.ico"
!define MUI_UNICON "..\resources\icon.ico"

; 欢迎页
!define MUI_WELCOMEPAGE_TITLE "欢迎使用 ${APP_NAME} 安装向导"
!define MUI_WELCOMEPAGE_TEXT "本向导将指引您安装 ${APP_NAME} v${APP_VERSION}。$\r$\n$\r$\n建议在安装前关闭其他正在运行的程序。$\r$\n$\r$\n点击【下一步】继续。"

; 完成页
!define MUI_FINISHPAGE_TITLE "安装完成"
!define MUI_FINISHPAGE_TEXT "${APP_NAME} 已成功安装到您的计算机。$\r$\n$\r$\n勾选下方选项可立即启动程序。"
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "运行 ${APP_NAME}"

; 安装页面顺序
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; 卸载页面
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 语言
!insertmacro MUI_LANGUAGE "SimpChinese"

; ------------------------------------------------------------
; 安装区段 - 主程序
; ------------------------------------------------------------
Section "主程序" SecMain
    SectionIn RO

    SetOutPath $INSTDIR

    ; 复制 PyInstaller 打包的全部文件（含 _internal/）
    File /r "..\dist\河北高考志愿填报系统\*.*"

    ; 创建快捷方式（用户目录）
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0

    ; 写入注册表 - 安装路径（用户级别）
    WriteRegStr HKCU "Software\${COMP_NAME}" "InstallPath" "$INSTDIR"

    ; 写入卸载信息（用户级别）
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMP_NAME}" \
        "DisplayName" "${APP_NAME}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMP_NAME}" \
        "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMP_NAME}" \
        "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMP_NAME}" \
        "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMP_NAME}" \
        "InstallLocation" "$\"$INSTDIR$\""
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMP_NAME}" \
        "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMP_NAME}" \
        "NoRepair" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMP_NAME}" \
        "EstimatedSize" 82000

    ; 写入卸载程序
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; ------------------------------------------------------------
; 卸载区段
; ------------------------------------------------------------
Section "Uninstall"
    ; 删除所有已安装文件
    RMDir /r "$INSTDIR"

    ; 删除快捷方式
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    Delete "$DESKTOP\${APP_NAME}.lnk"

    ; 清理注册表（用户级别）
    DeleteRegKey HKCU "Software\${COMP_NAME}"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMP_NAME}"
SectionEnd
