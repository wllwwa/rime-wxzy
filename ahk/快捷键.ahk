#Requires AutoHotkey v2.0
SetCapsLockState "AlwaysOff"
InstallKeybdHook


; 添加Shift+CapsLock切换大写锁定状态
+CapsLock:: {
    static CapsLockToggled := false
    CapsLockToggled := !CapsLockToggled
    if CapsLockToggled {
        SetCapsLockState "AlwaysOn"
        TrayTip "大写锁定", "已开启", 1
    } else {
        SetCapsLockState "AlwaysOff"
        TrayTip "大写锁定", "已关闭", 1
    }
}

CapsLock::return

CapsLockNumpadSend(key, num) {
    Send "{RCtrl Down}"
    Send "{" num "}"
    KeyWait key
    Send "{RCtrl Up}"
}

; 热键映射（F区映射）
CapsLock & u:: CapsLockNumpadSend("u", "F13") ;快捷键caplock+u 回退至第一音节后
CapsLock & i:: CapsLockNumpadSend("i", "F14") ;快捷键caplock+i 回退至第二音节后
CapsLock & o:: CapsLockNumpadSend("o", "F15") ;快捷键caplock+o 回退至第三音节后
CapsLock & p:: CapsLockNumpadSend("p", "F16") ;快捷键caplock+p 回退至第四音节后
CapsLock & a:: CapsLockNumpadSend("a", "F18") ;快捷键caplock+a 切换顶功整句
CapsLock & q:: CapsLockNumpadSend("q", "F19") ;快捷键caplock+q 快捷自造词
CapsLock & f:: CapsLockNumpadSend("f", "F20") ;快捷键caplock+f 切换方案
CapsLock & e:: CapsLockNumpadSend("e", "F11")
CapsLock & b:: CapsLockNumpadSend("b", "F12")
CapsLock & s:: CapsLockNumpadSend("s", "F10")

CapsLock & j::Send "{Left}"
CapsLock & k::Send "{Right}"
CapsLock & h::Send "{Home}"
CapsLock & l::Send "{End}"
CapsLock & n::Send "{Up}"
CapsLock & m::Send "{Down}"





