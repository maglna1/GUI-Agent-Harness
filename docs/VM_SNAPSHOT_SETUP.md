# OSWorld VM 快照配置指南

> 在新机器上从零配置 VM + 拍 `init_state` 快照的完整清单。
> 最后更新：2026-04-18

---

## 为什么需要这份文档

`init_state` 是每道题跑之前 `vmrun revertToSnapshot` 要恢复到的"干净起始状态"。这个快照的质量直接决定了测试能不能跑、结果稳不稳定。

**常见坑**：
- 带内存状态的快照在**不同 Apple Silicon 芯片间不兼容**（会报 `arm64.ssbs2` 错误）
- 必要服务没开机自启，VM 恢复后 HTTP API 连不上
- 预装应用缺失，某些任务跑不起来
- 干扰元素（自动更新弹窗、锁屏）让 agent 看到的画面不稳定

---

## 最推荐做法：用 OSWorld 官方镜像

**不要自己从 Ubuntu ISO 装**，直接用官方预装镜像。

### 步骤

1. 下载 OSWorld 官方 VM：https://huggingface.co/datasets/xlangai/osworld
   - 文件名：`Ubuntu-arm.zip`（Apple Silicon 用）或 `Ubuntu.zip`（Intel 用）
   - 约 15GB 压缩包

2. 解压到固定路径：

   ```bash
   mkdir -p ~/OSWorld/vmware_vm_data
   cd ~/OSWorld/vmware_vm_data
   unzip ~/Downloads/Ubuntu-arm.zip
   # 确认得到 ~/OSWorld/vmware_vm_data/Ubuntu-arm/ 目录
   ```

3. 双击 `Ubuntu.vmx` 打开。VMware 弹窗 "Did you move or copy this virtual machine?" → 选 **"I Copied It"**

4. 第一次开机，确认能正常进桌面（用户名 `user`，密码 `password`）

5. 关机（**不是挂起**）：
   ```bash
   /Applications/VMware\ Fusion.app/Contents/Public/vmrun \
     stop ~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx
   ```

6. 拍 `init_state` 冷快照：
   ```bash
   /Applications/VMware\ Fusion.app/Contents/Public/vmrun \
     snapshot ~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx init_state
   ```

7. 验证：
   ```bash
   /Applications/VMware\ Fusion.app/Contents/Public/vmrun \
     listSnapshots ~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx
   # 应该看到：
   # Total snapshots: 1
   # init_state
   ```

搞定。下面的"必须项"官方镜像都装好了。

---

## 如果自己装 VM，必须配置这些

### 1. 预装应用

全部必须可用，不然对应 domain 的测试跑不了：

| 应用 | 用途 | 安装 | 验证 |
|------|------|------|------|
| Chromium (snap) | Chrome / Multi-Apps | `sudo snap install chromium` | `which chromium` |
| LibreOffice | Writer/Calc/Impress | `sudo apt install libreoffice` | `libreoffice --version` |
| GIMP | GIMP domain | `sudo apt install gimp` | `gimp --version` |
| VS Code | VS Code domain | 官网 .deb 包 | `code --version` |
| VLC | VLC domain | `sudo apt install vlc` | `vlc --version` |
| Thunderbird | Thunderbird domain | `sudo apt install thunderbird` | `thunderbird --version` |
| Python 3 + pyautogui | setup 里的 execute | `pip install pyautogui` | `python3 -c "import pyautogui"` |
| socat | CDP 端口转发 (9222→1337) | `sudo apt install socat` | `which socat` |
| wmctrl, xdotool | setup 里的窗口操作 | `sudo apt install wmctrl xdotool` | `which wmctrl xdotool` |
| xrandr | 调分辨率 | 通常自带 | `which xrandr` |
| curl, ffmpeg | 辅助工具 | `sudo apt install curl ffmpeg` | - |

### 2. OSWorld Flask Server 开机自启（**最关键**）

VM 里必须有一个 Flask server 监听 `0.0.0.0:5000`，提供截图、执行命令等 HTTP API。源码在 OSWorld 仓库的 `virtual_machine/` 目录。

**验证**：在宿主机上跑

```bash
curl http://172.16.82.132:5000/screenshot -o /tmp/test.png
# 能拿到截图 = OK
```

**用 systemd 保证开机自启**：

```bash
sudo tee /etc/systemd/system/osworld-server.service <<'EOF'
[Unit]
Description=OSWorld HTTP API Server
After=graphical.target network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/osworld
ExecStart=/usr/bin/python3 /home/user/osworld/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
EOF

sudo systemctl enable osworld-server
sudo systemctl start osworld-server
sudo systemctl status osworld-server  # 看是不是 active
```

### 3. 用户配置

- 用户名 **`user`**，密码 **`password`**（脚本里硬编码）
- **开机自动登录**到桌面（不然每次启动卡在密码输入）

自动登录配置（Ubuntu GNOME）：

```bash
sudo vim /etc/gdm3/custom.conf
# 加两行：
# AutomaticLoginEnable=true
# AutomaticLogin=user
```

### 4. 分辨率 1920×1080

GUI agent 按这个分辨率算坐标。

```bash
# 装 open-vm-tools（让 VMware 能调整分辨率）
sudo apt install open-vm-tools open-vm-tools-desktop

# 设默认分辨率
xrandr --output Virtual-1 --mode 1920x1080
```

在 VMware Fusion 里也要设显示器为 1920×1080。

### 5. 网络

- 用 VMware NAT 模式（默认）
- 确认 `ifconfig` 能看到 IP
- VM 能 ping 通宿主机 `172.16.82.1`

如果用代理访问外网：脚本每次会自动写 `/etc/profile.d/proxy.sh`，**快照里不用预配置**。

---

## 推荐配置（提高稳定性）

这些不是必须，但强烈建议在快照前做：

### 6. 关掉干扰元素

```bash
# 禁用自动更新弹窗
sudo apt remove update-notifier
sudo systemctl disable apt-daily.timer apt-daily-upgrade.timer

# 关闭屏幕保护和锁屏
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false

# 关闭自动休眠
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 0

# 关闭通知气泡
gsettings set org.gnome.desktop.notifications show-banners false
```

### 7. 应用首次运行向导跑完

让 Chromium / LibreOffice / VS Code 等都**打开一次**，跑完首次运行的欢迎/导入向导，再关掉。否则测试时这些向导弹出来会挡 agent。

```bash
# Chromium 首次向导
chromium --no-first-run &
sleep 5
pkill chromium

# LibreOffice 首次向导
libreoffice --writer &
sleep 10
pkill soffice

# 其他同理
```

### 8. 干净桌面

快照前确保：

- ✅ 已登录进桌面（不是锁屏界面）
- ✅ **没有任何应用窗口打开**（浏览器、文件管理器、终端都关掉）
- ✅ 没有系统通知气泡
- ✅ 任务栏 / Dock 在默认位置
- ✅ 桌面壁纸是默认的

---

## 不用配置的（脚本会自动做）

这些每道题跑之前 `setup_vm()` 都会重做，快照里**不要**预配置：

| 动作 | 脚本位置 |
|------|----------|
| 装 `/usr/local/bin/google-chrome` 到 chromium 的 wrapper | `benchmarks/osworld/run_osworld_task.py:89-93` |
| 写 `/etc/profile.d/proxy.sh` 系统代理 | `run_osworld_task.py:104-108` |
| xrandr 1920×1080 | `run_osworld_task.py:117` |
| 下载任务文件、打开应用 | `SetupController.setup(config)` |

预先写这些反而可能被脚本覆盖，或在别的任务里干扰。

---

## 拍快照的正确流程（踩坑避免）

### ⚠️ 一定要冷关机后拍

带内存状态的快照（`.vmem` 文件）会**绑定当时的 CPU 特性**。不同 Apple Silicon 芯片（M1/M2/M3/M4）的 CPU 特性不完全一样。源机器是 M3 拍的，目标机器是 M1 就可能报：

```
VM requirements not satisfied by host:
arm64.ssbs
arm64.ssbs2
```

**只有 VM 关机状态拍的快照**能跨芯片用。

### 标准流程

```bash
VMX=~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx
VMRUN=/Applications/VMware\ Fusion.app/Contents/Public/vmrun

# 1. VM 完全关机（soft shutdown，系统正常退出）
$VMRUN stop "$VMX"
# 如果卡住就强制关：
# $VMRUN stop "$VMX" hard

# 2. 等几秒确认进程退出
sleep 5
$VMRUN list  # 列表不应该包含这个 VMX

# 3. 删旧快照
$VMRUN deleteSnapshot "$VMX" init_state

# 4. 拍新快照（此时 VM 关机，拍的是冷快照）
$VMRUN snapshot "$VMX" init_state

# 5. 验证
$VMRUN listSnapshots "$VMX"
# 输出：
# Total snapshots: 1
# init_state
```

### 拍完快照后验证

```bash
# 启动 VM
$VMRUN start "$VMX" gui

# 等 VM 启动（约 30 秒）
sleep 30

# 检查 Flask server
curl http://172.16.82.132:5000/screenshot -o /tmp/test.png
ls -la /tmp/test.png  # 有文件且大小 > 0 就 OK

# 跑一个冒烟测试
cd /path/to/GUI-Agent-Harness
python benchmarks/osworld/run_osworld_task.py 1 --domain os --max-steps 10
```

---

## 完整 Checklist（给配置者打勾用）

### VM 内部

- [ ] 用户 `user` / 密码 `password` 能登录
- [ ] 开机自动登录到桌面
- [ ] 分辨率 1920×1080
- [ ] 装好：Chromium / LibreOffice / GIMP / VS Code / VLC / Thunderbird
- [ ] 装好：Python3 + pyautogui / socat / wmctrl / xdotool / xrandr / curl / ffmpeg
- [ ] OSWorld Flask server 开机自启，宿主机能 `curl :5000/screenshot`
- [ ] 关闭自动更新弹窗
- [ ] 关闭屏幕保护和锁屏
- [ ] 关闭自动休眠
- [ ] 所有应用首次运行向导都跑完
- [ ] 桌面干净（无窗口、无通知）

### 快照流程

- [ ] VM **完全关机**（不是挂起）
- [ ] `$VMRUN list` 不包含该 VMX
- [ ] 删掉旧 `init_state`
- [ ] 创建新 `init_state`
- [ ] `listSnapshots` 能看到 `init_state`

### 拍完验证

- [ ] `vmrun revertToSnapshot init_state` 能恢复
- [ ] VM 启动后 `curl :5000/screenshot` 成功
- [ ] 冒烟测试跑通至少 1 道题

全部打勾，快照就算配好了。

---

## 文件位置速查

| 文件 | 路径 |
|------|------|
| 本文档 | `docs/VM_SNAPSHOT_SETUP.md` |
| VM 目录 | `~/OSWorld/vmware_vm_data/Ubuntu-arm/` |
| VMX 配置 | `~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx` |
| 快照元数据 | `~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmsd` |
| vmrun CLI | `/Applications/VMware Fusion.app/Contents/Public/vmrun` |
| OSWorld 官方镜像 | https://huggingface.co/datasets/xlangai/osworld |
| 相关文档 | `docs/VM_SETUP.md`（VM 整体架构和 setup 流程） |
