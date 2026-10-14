# 3x-ui · No Ads

[MHSanaei/3x-ui](https://github.com/MHSanaei/3x-ui) 的非官方去广告构建。保留原项目功能、许可证和归属；移除面板赞助商菜单、页面、登录/总览/侧栏广告和远程赞助商接口。

每次同步还会清理各语言及子目录 README 的赞助、捐款、付费推广章节，并移除 GitHub Sponsor 入口。维护规则见 [AGENTS.md](AGENTS.md)。同步时从本仓库当前 `main` 恢复 `AGENTS.md`、`.noads/`、自动发布流程和本页，按字节检查保留结果，避免被上游覆盖。无法识别的推广链接或补丁冲突会停止发布，修正规则后再重试。

## 安装与更新

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xinian5216/3x-ui-private/main/install.sh)
```

现有面板迁移前请备份数据库和设置。使用上述安装器更新后，面板更新和 `x-ui` 更新菜单均跟随本仓库。Release 的版本号与上游保持一致，发布标题和随包 `NOADS.md` 标明修改版。不要切换到 Dev 更新通道：此仓库仅发布正式版本。

- [下载经过检查的安装包](https://github.com/xinian5216/3x-ui-private/releases/latest)
- [自动同步与构建状态](https://github.com/xinian5216/3x-ui-private/actions/workflows/noads-sync.yml)
- [上游使用文档](https://docs.sanaei.dev)

## 自动维护

每小时第 17 分钟检查上游正式 Release，从 v3.10.0 起按版本顺序补齐尚未发布的版本；也支持手动运行。补丁、广告检查、密钥检查、前端和 Go 测试及全部 7 个 Linux 架构与 Windows amd64 构建全部通过后，才公开完整 Release。

同步源码先进入临时构建分支；所有检查、构建和附件上传通过后，才更新 main 并公开 Release。上游改动导致补丁不适用、出现新的凭据候选或构建失败时，流程停止，main 的安装/更新脚本和上一版 Release 均保留；可通过 Actions 查看失败原因。需要修补规则后重新运行，不能保证未来广告形式变化时完全无需维护。

GitHub 定时运行可能延迟，公开仓库连续 60 天无活动时会停用定时工作流；在 Actions 重新启用即可。未配置外部常驻服务或保活提交。

源码版本和上游提交记录在 [.noads/provenance.json](.noads/provenance.json)。构建使用对应上游 Release 的官方构建步骤和依赖版本；不会复制上游面板二进制作为去广告安装包。现有旧标签保留历史用途，并不代表去广告 Release；请从 Releases 页面下载。

## 许可证

遵循 [GPL-3.0](LICENSE)。这是非官方修改版本，不是上游作者发布或支持的版本。修改说明见 [NOADS.md](NOADS.md)，源码随对应 Release 标签公开。
