# Phase 6 Handoff — Planning Only / Pending Deployment Approval

Status: Local PASS / Cloud VM Option C PASS / Public TLS Pending  
規則：Local smoke + gate drill 已 PASS；Cloud VM Option C（repo deploy + container-local validation）已 PASS；public domain/TLS first deploy 尚未完成。

---

## 1. Planning Summary

Phase 6 planning、first deploy runbook、local smoke test、QA Validate 均已完成。Cloud VM `layerstack` Option C 已完成，且已依 User 要求改為 `ubuntu` login + user-home data root：repo deployed to `/home/ubuntu/projects/doc-infra`，data root `${HOME}/doc-infra-data`，container nginx + SFTPGo + gate validate/stage/promote/rollback verified。

建議下一步：

```text
設定 SFTPGo admin/user/group/virtual folder（manual first-run provisioning）
取得 User 核准後安裝/設定 Host Nginx + certbot
提供 domain/DNS 後重新執行 public HTTPS validation
```

---

## 2. Files Created

| 檔案 | 說明 |
|---|---|
| `task_plan.md` | Phase 6 planning-only task plan |
| `developer_prompt.md` | Future implementation/deployment prompt draft |
| `development_log.md` | Planning log |
| `phase_handoff.md` | 本文件 |
| `docs/arch/first_deploy_operational_runbook.md` | First deploy operational runbook |
| `README.md` | Phase 6 quick reference |

---

## 3. Proposed Scope

| Scope | Included? |
|---|---:|
| First deploy runbook | ✅ |
| Local smoke test | ✅ |
| code-reviewer E2E drill | ✅ |
| rollback drill | ✅ |
| Cloud VM/domain/TLS validation | Optional / depends on User inputs |
| Multi-project support | ❌ |
| SFTPGo event automation | ❌ |
| Review UI | ❌ |
| Pagefind | ❌ |

---

## 4. Approval Checklist

User 需確認：

- [x] Local smoke test completed and PASS。
- [x] Cloud VM SSH access verified for `layerstack`。
- [x] 是否核准將 doc-infra repo 部署到 VM。
- [ ] 是否提供正式 domain / DNS A record。
- [ ] 是否允許安裝與設定 Host Nginx/certbot。
- [x] 是否調查/修復 SFTPGo container restarting。
- [ ] 是否設定 SFTPGo first-run admin/user/group。

---

## 5. Known Preconditions

1. Phase 5 PASS。
2. `code-reviewer` 是唯一完整 MVP pilot。
3. SFTPGo 仍 localhost-only。
4. Broken symlink minor 尚未修；不阻塞 first deploy，但需記錄。
5. Cloud VM actual state 未知。

---

## 6. Next Step

等待 User 決定：

```text
Approve SFTPGo first-run admin/user/group setup guidance.
```

或：

```text
Approve Host Nginx + certbot installation/configuration.
Domain: ...
DNS A record status: ...
```
