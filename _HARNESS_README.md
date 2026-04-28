# 📌 이 폴더는 NAS 작업본입니다

이 폴더(`AirDome_3D_Viewer_R14`)는 **AirDome 3D Viewer 프로젝트의 NAS 작업본**입니다.
2026-04-28 하네스 시스템에 편입되었으며, 코드 변경 이력은 별도 Git으로 추적됩니다.

## 🗂 3-위치 구조

| 위치 | 역할 | 경로 |
|---|---|---|
| **여기 (NAS)** | 실제 작업본 (메인) | `X:\05. My_Assistant\06. Hanness_System\03. Project\OZOMETA\윤해범 교수님\AirDome_3D_Viewer_R14\` |
| **로컬 Git** | 변경 이력 추적 사본 | `C:\Users\NAMGUNGSUK\Projects\airdome-3d-viewer\` |
| **GitHub Private** | 이력 마스터 + 다중 PC 공유 | https://github.com/NGS1024/airdome-3d-viewer |
| **NAS 박제 백업** | "절대 안 건드릴" 2026-04-28 시점 원본 | `..\_backup\AirDome_3D_Viewer_R14_v0_2026-04-28\` |

## 🔄 작업 흐름

```
[수정 시]
  NAS (여기) 에서 코드 수정
    ↓
  변경분을 로컬 Git 폴더(C:\Users\NAMGUNGSUK\Projects\airdome-3d-viewer\) 에 반영
    ↓
  git add → commit → push
    ↓
  GitHub에 이력 누적

[다른 PC에서 이어가기]
  git -C C:\Dev\claude-workspace pull             # 규칙·지식
  git -C C:\Users\NAMGUNGSUK\Projects\airdome-3d-viewer pull   # 코드 이력
  NAS 마운트되어 있으면 이 폴더로 즉시 작업 가능
```

## ⚠️ 주의

- 이 폴더에서 직접 `git init` 하지 마세요 (NAS 네트워크 드라이브에서 git은 속도 저하).
  → 변경 이력 관리는 **로컬 Git 폴더**에서 합니다.
- `__pycache__/`, `.vs/`, `.vscode/` 등은 `.gitignore` 처리되어 GitHub에 안 올라갑니다.

## 📚 관련 문서

- 프로젝트 규칙: `C:\Dev\claude-workspace\projects\ozometa-prof-yoon-airdome\CLAUDE.md`
- GitHub 셋업 상세: `C:\Dev\claude-workspace\projects\ozometa-prof-yoon-airdome\knowledge\github-setup.md`
- 작업 로그(현장): `..\knowledge\work-log.md` (작성 예정)
- 사용자용 설치 가이드: `README_설치가이드.txt` (이 폴더에 있음, 별개 문서)

---

> 🤖 이 파일은 Claude Code가 2026-04-28 하네스 편입 작업 중 자동 생성했습니다.
> 변경 시 위 3-위치 구조 일관성을 유지해 주세요.
