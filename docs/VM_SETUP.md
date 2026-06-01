# OSWorld VM 与 Setup 机制详解

> 给第二个 agent 看的实战文档。讲清楚 VM 到底是怎么管的、每个任务跑之前发生了什么。
> 最后更新：2026-04-17

---

## TL;DR（3 句话版）

1. 整个 Ubuntu VM 就是 `~/OSWorld/vmware_vm_data/Ubuntu-arm/` 这一个目录，约 33GB
2. 目录里有一个叫 `init_state` 的**快照**，每跑一道题前会 `vmrun revertToSnapshot` 回到这个干净状态
3. revert 完后，脚本再做一堆**环境配置**（代理、Chromium wrapper、分辨率）+ 跑 OSWorld 官方的 **task setup**（下载文件、打开应用），最后才让 agent 开始干活

---

## 1. VM 文件结构

路径：`~/OSWorld/vmware_vm_data/Ubuntu-arm/`

```
Ubuntu.vmx                      # VM 配置文件（vmrun 参数就是指这个）
Ubuntu.vmsd                     # 快照元数据（明文，能 cat 看）
Ubuntu-Snapshot44.vmsn          # init_state 快照的 CPU/设备状态（4.5MB）
Ubuntu-Snapshot44.vmem          # init_state 快照的内存镜像（2.8GB）
Ubuntu-f265a4fc.vmem            # 当前运行时内存（4GB，VM 跑着的时候才有）
Ubuntu-f265a4fc.vmss            # 当前运行时暂停状态
Ubuntu.nvram                    # BIOS/NVRAM
Virtual Disk-000001-s001.vmdk   # 硬盘分片（多个文件，一起构成硬盘）
Virtual Disk-000001-s002.vmdk
...
```

### 1.1 快照是怎么记录的

`Ubuntu.vmsd` 是明文的配置文件，长这样：

```
.encoding = "UTF-8"
snapshot.lastUID = "44"
snapshot.current = "44"
snapshot0.uid = "44"
snapshot0.filename = "Ubuntu-Snapshot44.vmsn"
snapshot0.displayName = "init_state"     ← 关键：快照名
snapshot0.description = ""
snapshot0.type = "1"
snapshot0.numDisks = "1"
snapshot0.disk0.fileName = "Virtual Disk.vmdk"
snapshot.numSnapshots = "1"
```

脚本跑 `vmrun revertToSnapshot VMX init_state` 时，VMware 就是根据这个文件找到对应的 `.vmsn` 和 `.vmem` 加载回去的。

### 1.2 迁移 VM 到新机器

**只要整个 `~/OSWorld/vmware_vm_data/Ubuntu-arm/` 目录拷过去**，路径保持一样，就能直接用。约 33GB。

```bash
# 在旧机器打包（可选，省空间）
cd ~/OSWorld/vmware_vm_data
tar czf Ubuntu-arm.tar.gz Ubuntu-arm/

# 传到新机器（网速慢就用移动硬盘）
scp Ubuntu-arm.tar.gz newmachine:~/OSWorld/vmware_vm_data/
# 或 rsync
rsync -avP Ubuntu-arm/ newmachine:~/OSWorld/vmware_vm_data/Ubuntu-arm/

# 在新机器解压
cd ~/OSWorld/vmware_vm_data
tar xzf Ubuntu-arm.tar.gz
```

拷完后：

1. 新机器装 **VMware Fusion**
2. 双击 `Ubuntu.vmx` 打开 VM，或用 `vmrun start` 启动
3. 第一次启动 VMware 可能问 "Did you move or copy this virtual machine?" → 选 **"I Copied It"**（保留 MAC 地址，避免 IP 变）
4. VM 启动后 `ifconfig` 看 IP，如果不是默认的 `172.16.82.132`，跑命令时加 `--vm <新IP>`

---

## 2. 每个任务的完整 Setup 流程

所有逻辑都在 `benchmarks/osworld/run_osworld_task.py` 的 `setup_vm()` 函数里。分两大阶段：

### 阶段 A：**我们自己**的 VM 预备（硬编码）

这部分是为了修 OSWorld 官方没考虑到的坑。

#### A1. Revert 到 init_state 快照

```python
subprocess.run([VMRUN, "revertToSnapshot", VMX, "init_state"])
subprocess.Popen([VMRUN, "start", VMX, "gui"])  # gui 模式启动
time.sleep(5)
```

**为什么 revert**：每个任务都在同一干净起点跑，上一题的文件、进程、浏览器历史都清掉。

#### A2. 等 VM HTTP API 上线

```python
vm_url = f"http://{vm_ip}:5000"
for i in range(60):
    try:
        urllib.request.urlopen(f"{vm_url}/screenshot", timeout=5)
        time.sleep(3)
        break
    except Exception:
        time.sleep(3)
```

VM 里跑着一个 Flask server（OSWorld 预装的），监听 5000 端口，提供 `/screenshot`、`/execute`、`/file` 等 API。等它能响应了再继续。

#### A3. 装 Chromium wrapper（重要）

```bash
# 在 VM 里执行
sudo bash -c '
printf "#!/bin/bash\nexec /snap/bin/chromium --remote-debugging-port=1337 \"\$@\"\n" \
  > /usr/local/bin/google-chrome && chmod +x /usr/local/bin/google-chrome'
```

**为什么**：OSWorld 的 evaluator 要 `google-chrome` 命令，但 VM 只装了 snap `chromium`。我们在 `/usr/local/bin/google-chrome` 放一个 shim 脚本，指向真正的 chromium，并且加上 `--remote-debugging-port=1337` 让 evaluator 能通过 CDP 看 tab。

#### A4. 配系统级代理

```bash
# 写入 /etc/profile.d/proxy.sh
export HTTP_PROXY=http://172.16.82.1:6152
export HTTPS_PROXY=http://172.16.82.1:6152
export http_proxy=http://172.16.82.1:6152
export https_proxy=http://172.16.82.1:6152

# 也追加到 ~/.bashrc
```

**为什么**：
- `172.16.82.1` 是 macOS 宿主机在 VMware NAT 网络里的地址
- 宿主机上跑着 Surge，监听 6152 端口
- 这样 VM 里所有程序（curl、apt、pip、VS Code）都能通过宿主机的 Surge 访问外网

#### A5. 设分辨率

```bash
xrandr --output Virtual-1 --mode 1920x1080
```

**为什么**：init_state 快照里可能是非标准分辨率，GUI agent 要 1920×1080 才能正确定位。

---

### 阶段 B：OSWorld 官方 task setup（每题不同）

每道题的 JSON 里有一个 `config` 数组，按顺序执行。脚本把它交给 OSWorld 的 `SetupController`：

```python
from desktop_env.controllers.setup import SetupController
setup_controller = SetupController(
    vm_ip=vm_ip, server_port=5000,
    chromium_port=9222, vlc_port=8080,
    cache_dir="cache", client_password="password",
    screen_width=1920, screen_height=1080,
)
setup_controller.setup(config, use_proxy=use_proxy)
```

`config` 数组里的每一项是一个**步骤**，`type` 决定怎么执行。常见 type：

| type | 作用 | 例子 |
|------|------|------|
| `download` | 从 URL 下载文件到 VM 里的指定路径 | 下载 `report.xlsx` 到 `/home/user/Documents/` |
| `open` | 用默认程序打开一个文件 | 打开 LibreOffice Writer 文档 |
| `launch` | 启动指定命令 | `google-chrome --new-window https://github.com` |
| `execute` | 在 VM 里跑 shell/python 命令 | `pyautogui.hotkey('f11')` |
| `command` | 跑 shell 命令（类似 execute 但更简单） | `mkdir -p /home/user/Documents/foo` |
| `sleep` | 等 N 秒 | 等 UI 加载完 |
| `activate_window` | 把某个窗口切到前台 | 让 Chromium 成为焦点 |
| `chrome_open_tabs` | 在 Chrome 里打开一堆 URL | 开 GitHub + Docs 两个 tab |
| `proxy` | 在 VM 里起 tinyproxy（内部代理） | 给需要代理的任务用 |
| `googledrive` | 登录 Google Drive | 少数需要云盘的任务 |

#### 典型 task config 长这样

```json
{
  "id": "00fa164e-2612-4439-992e-157d019a8436",
  "snapshot": "libreoffice_writer",
  "instruction": "把 expe-results.xlsx 里 GPT-4 的结果抽出来插到报告里...",
  "config": [
    {
      "type": "command",
      "parameters": {"command": ["mkdir", "-p", "/home/user/Documents/awesome-desktop/"]}
    },
    {
      "type": "download",
      "parameters": {
        "files": [
          {"path": "/home/user/Documents/awesome-desktop/awe_desk_env.docx",
           "url": "https://huggingface.co/.../awe_desk_env.docx"},
          {"path": "/home/user/Documents/awesome-desktop/expe-results.xlsx",
           "url": "https://huggingface.co/.../results.xlsx"}
        ]
      }
    },
    {
      "type": "open",
      "parameters": {"path": "/home/user/Documents/awesome-desktop/awe_desk_env.docx"}
    }
  ],
  "related_apps": ["libreoffice_writer"],
  "evaluator": { ... }
}
```

跑完 setup 后，VM 里就是：两个文件已经下好了，文档已经在 LibreOffice 里打开了，agent 一上场就能看到屏幕。

---

## 3. 整个运行流程时序图

```
[主脚本 run_osworld_task.py]
    │
    ├─ get_task_config(task_num)        读 OSWorld JSON
    │
    ├─ setup_vm(vm_ip, task_config)
    │    │
    │    ├─ vmrun revertToSnapshot init_state   ← 回到干净状态
    │    ├─ vmrun start (GUI mode)
    │    ├─ 等 http://VM:5000/screenshot 响应
    │    ├─ 装 /usr/local/bin/google-chrome shim
    │    ├─ 写 /etc/profile.d/proxy.sh
    │    ├─ xrandr 1920x1080
    │    └─ SetupController.setup(config)
    │         └─ 依次执行 download / open / launch / execute 步骤
    │
    ├─ run_task(task_config, vm_ip, max_steps)
    │    │
    │    ├─ patch_for_vm(VM_URL)                 让截屏/点击走 VM HTTP
    │    ├─ wmctrl -a Chromium                    把浏览器置顶（如果是 Chrome 任务）
    │    └─ execute_task(...)                    ← gui_agent() 4-phase 循环开始
    │
    ├─ [diag] 打印 CDP 端口状态                  evaluator 前自检
    │
    └─ subprocess.run(eval_osworld_task.py)      跑 OSWorld 官方 evaluator 打分
```

---

## 4. 手动操作 VM（开发 / 调试常用）

### 4.1 手动 revert

```bash
/Applications/VMware\ Fusion.app/Contents/Public/vmrun \
  revertToSnapshot ~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx init_state

/Applications/VMware\ Fusion.app/Contents/Public/vmrun \
  start ~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx gui
```

### 4.2 看现在有哪些快照

```bash
/Applications/VMware\ Fusion.app/Contents/Public/vmrun \
  listSnapshots ~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx
# 输出：
# Total snapshots: 1
# init_state
```

### 4.3 自己创建新快照（比如配好环境想存起来）

```bash
# 先让 VM 进入想保存的状态
/Applications/VMware\ Fusion.app/Contents/Public/vmrun \
  snapshot ~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx my_new_snapshot
```

⚠️ **不要删除 `init_state` 快照**，整套脚本靠它来重置。

### 4.4 通过 HTTP API 直接操作 VM

VM 里跑着 OSWorld 的 Flask server（端口 5000）。常用端点：

```bash
# 截屏
curl http://172.16.82.132:5000/screenshot -o /tmp/vm.png

# 在 VM 里跑命令
curl -X POST http://172.16.82.132:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la /home/user/Desktop", "shell": true}'

# 读 VM 里的文件
curl http://172.16.82.132:5000/file -G \
  --data-urlencode "file_path=/home/user/Desktop/report.txt" \
  -o /tmp/report.txt
```

---

## 5. 故障排查

### 5.1 VM 启动后连不上 5000 端口

可能原因：
- VM IP 变了 → `ifconfig` 看新 IP，用 `--vm` 指定
- Flask server 没起来 → 进 VM 看一下 `systemctl status osworld-server`（具体服务名看你 VM 里的配置）
- 防火墙挡了 → VM 里 `sudo ufw disable`

### 5.2 revertToSnapshot 超时

脚本有 120 秒超时。如果机器慢：
- 可能真的需要更长，但通常是 VM 进程被卡住了
- 手动跑 `vmrun stop ... hard` 先强制关，再 revert

### 5.3 evaluator 报 "could not connect to Chrome"

Chromium wrapper 没装好 / 没加 `--remote-debugging-port=1337`。现在代码已经加了，但如果改过 wrapper 要确认。手动检查：

```bash
curl http://VM_IP:5000/execute -X POST \
  -H "Content-Type: application/json" \
  -d '{"command": "cat /usr/local/bin/google-chrome", "shell": true}'
# 应该看到 exec /snap/bin/chromium --remote-debugging-port=1337 "$@"
```

### 5.4 下载文件失败（setup 阶段）

通常是 VM 联不上网，检查：
- 宿主机 Surge 是不是在跑（端口 6152）
- `/etc/profile.d/proxy.sh` 是不是写进去了
- `curl -x http://172.16.82.1:6152 https://www.google.com` 在 VM 里能不能跑通

### 5.5 分辨率不对

init_state 快照里可能是别的分辨率。手动修：

```bash
# 在 VM 里
xrandr --output Virtual-1 --mode 1920x1080
# 或用脚本里的命令调
```

---

## 6. 关键常量速查

| 常量 | 值 | 在哪改 |
|------|----|--------|
| VMRUN | `/Applications/VMware Fusion.app/Contents/Public/vmrun` | `run_osworld_task.py:28` |
| VMX | `~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx` | `run_osworld_task.py:29` |
| VM_IP | `172.16.82.132` | CLI `--vm` 或 `run_osworld_task.py:287` |
| VM_PORT | 5000 | `run_osworld_task.py:27` |
| Snapshot name | `init_state` | `run_osworld_task.py:53` |
| PROXY_URL | `http://172.16.82.1:6152` | `run_osworld_task.py:75` |
| chromium_port | 9222 | `SetupController` 初始化 |
| Client password | `password` | `SetupController` 初始化 |
| Chromium debug port | 1337 | wrapper 脚本里 |

---

## 7. 给第二个 agent 的行动清单

如果你在新机器上要从零跑起来：

1. ✅ **装 VMware Fusion**
2. ✅ **把 `~/OSWorld/vmware_vm_data/Ubuntu-arm/` 拷过来**（33GB）
3. ✅ **Clone 这个仓库 + `pip install -e .`**
4. ✅ **Clone OSWorld + `pip install -e .`** 到 `~/OSWorld`
5. ✅ **装 Claude Code CLI + `claude login`**
6. ✅ **（可选）装 Surge，监听 6152 端口**
7. ✅ **启动 VM 一次，确认 IP 是 172.16.82.132**（或记下新 IP）
8. ✅ **确认 `init_state` 快照存在**：`vmrun listSnapshots .../Ubuntu.vmx`
9. ✅ **跑一个冒烟测试**：
   ```bash
   python benchmarks/osworld/run_osworld_task.py 1 --domain os --max-steps 10
   ```
10. 出错按第 5 节排查

每题的 JSON 文件都在 `~/OSWorld/evaluation_examples/examples/<domain>/<task_id>.json`，想看任务干什么就 `cat` 这个文件。
