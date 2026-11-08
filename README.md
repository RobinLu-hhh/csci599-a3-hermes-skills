# Hermes 示例天气 skill tap

原创 `a3-weather` 技能：查询洛杉矶**示例城市**今天、明天的真实 Open-Meteo 预报。日期采用 America/Los_Angeles，温度摄氏度、降雨概率百分比，回答保留来源和获取时间。无需课程账号、API key、邮箱或日历；脚本无缓存，不会读取私人资料。

## 快速使用

前提：可运行且已配置模型的 Hermes **v0.22.7**、Python 3.9+、IANA 时区/TLS CA 数据、`terminal` 工具及访问 `api.open-meteo.com` 的 HTTPS 网络。建议使用无生产凭据的独立 Hermes 环境。完整 Hermes 安装和模型下载另计，已有环境从安装技能到首个真实答案的目标为五分钟内，实际时间以安装记录为准。

```sh
hermes skills tap add RobinLu-hhh/csci599-a3-hermes-skills
hermes skills install RobinLu-hhh/csci599-a3-hermes-skills/a3-weather
hermes skills list
hermes chat -t skills,terminal -s a3-weather -q '请先读取 a3-weather 技能并实际运行随技能安装的 forecast.py 查询示例城市今天和明天的天气，然后完整引用本次工具 JSON 的 report 字段，保留两天数据与来源，不用示例数字。'
```

保留第三方技能的安全扫描结果；不要用 `--force` 绕过危险判定。技能在新会话中加载。固定版本 CLI 的安装命令没有 `--ref` 参数；复核时记录仓库完整 commit 和安装文件哈希，避免下载期间分支变动。

预期：Hermes 实际执行技能目录中的 `scripts/forecast.py`，从其 JSON 回答两个日期的 highC、lowC、rainProbabilityPct 和来源。数值随真实预报变化，下例只是字段结构，不能当实时天气：

```json
{"days":[{"date":"YYYY-MM-DD","highC":23,"lowC":15,"rainProbabilityPct":10}],"timezone":"America/Los_Angeles","fetchedAt":"UTC timestamp","source":"https://open-meteo.com/","cached":false,"stale":false}
```

## 工具与路径

`terminal` 是 Hermes 的命令执行工具，本身不等于只读沙箱。只读天气脚本使用固定 endpoint、不写文件；不要为安装本技能复制生产 OAuth、Google、Telegram 或 Tailscale 状态。

使用 `hermes chat --help` 确认 `-t/--toolsets`，上述命令显式启用 `skills,terminal`。技能载入时会把 `${HERMES_SKILL_DIR}` 换为绝对目录；也可用 `skill_view(name="a3-weather")` 的 `skill_dir` 字段定位，不依赖当前工作目录。独立脚本诊断：

```sh
python3 "$HERMES_HOME/skills/a3-weather/scripts/forecast.py"
```

若未设置 HERMES_HOME，以 `skill_view` 给出的绝对目录为准。直接运行脚本可诊断网络；正式使用仍须证明 Hermes 实际载入并调用技能。

## 故障排查

| 问题/代码 | 原因 | 修复 |
|---|---|---|
| 找不到 a3-weather 或 terminal | 技能未安装、会话未加载或工具禁用 | 检查 tap/list，开启新会话，使用上面的显式 toolsets 命令 |
| source_unavailable / source_rate_limited | 网络、TLS、超时或429 | 检查 HTTPS 网络和 Python CA，稍后重试；不能编造天气 |
| timezone_unavailable | 缺 IANA 时区数据 | 安装操作系统时区数据库或 Python tzdata |
| source_response_invalid | 上游 JSON、日期或数值不合法 | 保存错误 code 并稍后重试；不把错误叫作缓存 |

Python 未安装时先安装 Python；缺解释器时脚本不能产生 JSON。macOS 的 python.org Python 若缺 CA，请运行该 Python 安装附带的证书安装程序；不要关闭 TLS 验证。成功退出0；脚本可识别的源/数据失败退出3，stdout 是有限 JSON，包含 code/problem/cause/fix/docs，不打印服务响应正文或令牌。

## 版本、升级与重装

当前版本 1.0.3，固定参考环境 Hermes v0.22.7 / Python 3.14.9 Linux；标准库脚本另在 macOS Python 3.11 验证。其他 Hermes/操作系统组合未宣称通过。

更新前备份自己的技能修改和旧 commit。先查看 `hermes skills update --help`、`hermes skills uninstall --help`，使用当前 CLI 支持的操作；不要假定所有版本参数一致。更新后重新执行一次真实天气任务。失败可用 `hermes skills uninstall a3-weather` 后，从同一 tap 的上一已验收内容重装并核对文件哈希；仓库分支变动时先确认内容，不能用直链冒充 tap 安装。曾手工安装同名天气插件者应使用干净 HERMES_HOME，避免旧工具掩盖新安装失败。

## 许可与归属

代码 MIT，见 LICENSE；数据来源 [Open-Meteo](https://open-meteo.com/)，按 CC BY 4.0 署名。API依据 [Forecast文档](https://open-meteo.com/en/docs)；Hermes安装依据 [官方技能文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)。代码初稿、验证与 CLI 由 Codex 辅助，作者负责审查和验证。变更见 CHANGELOG.md；问题可在本仓库 Issues 提交，不要附带任何真实凭据或私密日志。
