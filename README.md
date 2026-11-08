# Fontconfig-list Lister (fclistLister)

TeX Live의 `fc-list` 결과를 GUI로 보여 주고, XeTeX/LuaTeX(fontspec)에서 바로 쓸 수 있는 **폰트 이름**을 복사하게 해 주는 작은 도구입니다. Windows 사용자 폰트를 TeX Live의 fontconfig가 인식하도록 `local.conf`를 자동으로 만들어 주는 기능도 있습니다.

- 버전: 2.0
- 제작: Nova de Hi and KTUG
- 라이선스: MIT (무료)
- 구현: Python 3.13, tkinter(Tcl/Tk), fontTools, Pillow

## 왜 만들었나

1. **한국어 Windows 콘솔에서 `fc-list` 결과를 알아볼 수 없다.**
   콘솔의 기본 코드 페이지(cp949)와 fontconfig의 UTF-8 출력이 맞지 않아 한글 폰트 이름이 깨져 보입니다. 이 도구는 출력을 UTF-8로 받아 GUI에 제대로 보여 줍니다.
2. **TeX Live의 XeTeX에 시스템·사용자 폰트(TeX Live 바깥의 폰트)를 알려 주는 `local.conf` 작성이 번거롭다.**
   fontconfig용 `local.conf`를 손으로 쓰고 `fc-cache`까지 돌리는 과정을 버튼 하나(`local.conf`)로 자동화했습니다.

## 주요 기능

| 기능 | 설명 |
| --- | --- |
| 폰트 목록 | `fc-list`로 설치된 폰트를 읽어 **폰트 이름 / 다른 이름 / 파일 이름** 세 열로 표시합니다. `.ttf` `.otf` `.ttc` `.otc` 파일만 대상입니다. |
| fontspec 이름 | 스타일이 Regular가 아니면 `패밀리 스타일` 형태(예: `Noto Serif CJK KR Bold`)로 조합해 보여 줍니다. |
| 검색·정렬 | 세 열 어디서든 검색할 수 있고, 열 머리글을 눌러 정렬합니다. |
| 복사 | 선택한 폰트의 이름 또는 파일 이름을 클립보드에 복사합니다. |
| 미리보기 | 폰트가 지원하는 글자에 맞춰 영문, 문장부호, 한글, 정자 한자, 간체 한자, 일본어 가나 샘플을 자동 구성해 보여 줍니다. |
| 폰트 정보 | fontTools로 `name` 테이블(Name ID 0–14 중 주요 항목), GSUB/GPOS **feature**, **script/language** 목록을 보여 줍니다. (`otfinfo -i`, `-s` 대체) |
| 파일 위치 열기 | 탐색기에서 파일을 선택 상태로 엽니다. Windows 시스템 글꼴 폴더의 폰트는 경로만 안내합니다. |
| `fc-cache` | TeX Live의 `fc-cache -frv`를 실행해 폰트 캐시를 갱신합니다. |
| `local.conf` | 아래 설명 참조. |

## `local.conf` 자동 설정

버튼 한 번으로 다음을 수행합니다.

1. `kpsewhich -var-value=TEXMFSYSVAR`로 TeX Live 시스템 변수 경로를 찾습니다.
2. 그 아래 `fonts/conf/local.conf`를 만들어, Windows 사용자 폰트 폴더
   `%LOCALAPPDATA%\Microsoft\Windows\Fonts`를 fontconfig 검색 경로로 등록합니다.
3. `fc-cache -f -v`로 캐시를 갱신합니다.

이후 `fc-list` 목록을 다시 불러오면(F3) 사용자 폰트가 나타나고, XeTeX에서 `\setmainfont{폰트 이름}`으로 쓸 수 있습니다.

참고:
- MiKTeX은 별도 설정이 필요 없어서 안내 메시지만 표시합니다.
- 쓰기 권한 문제로 실패하면 **관리자 권한**으로 다시 실행하세요.
- 기존 `local.conf`가 있으면 덮어씁니다. 직접 추가한 설정이 있다면 미리 백업하세요.

## 설치와 실행

필요한 것:
- TeX Live (`kpsewhich`, `fc-list`, `fc-cache`가 동작하는 환경)
- Python 3 (tkinter 포함)

```
pip install fonttools pillow
python fclistlister.py
```

실행하면 곧바로 폰트 목록을 불러옵니다.

## 사용법

1. 목록에서 폰트를 선택하면 아래 칸에 미리보기가 나타납니다. 위아래 경계를 끌어 크기를 조절할 수 있습니다.
2. 항목을 **우클릭**하면 다음 메뉴가 나옵니다.
   - 폰트 이름 복사
   - 파일 이름 복사
   - 폰트 정보 보기
   - 파일 위치로 열기
3. 사용자 폰트가 목록에 없으면 `local.conf` 버튼을 누른 뒤 `fc-list`(F3)를 다시 실행합니다.

### 단축키

| 키 | 동작 |
| --- | --- |
| F1 | 프로그램 정보 |
| F3 | `fc-list` 다시 불러오기 |
| Ctrl+F | 검색창으로 이동 |
| Ctrl+Enter | 폰트 이름 복사 |
| Alt+Enter | 파일 이름 복사 |
| Ctrl+I | 폰트 정보 보기 |
| Ctrl+Home / Ctrl+End | 목록 처음 / 끝으로 이동 |

## 알려진 제한

- 현재 **Windows 전용**입니다. 캐시 경로(`APPDATA`)와 `local.conf` 설정(`LOCALAPPDATA`)이 Windows 환경변수에 의존합니다.
- `fc-list`는 TeX Live의 실행 파일 폴더에서 찾으므로 TeX Live가 `PATH`에 잡혀 있어야 합니다.
- 미리보기는 TTC/OTC에는 적용되지 않습니다.
- 목록은 실행 시마다 `fc-list`로 새로 만들며, 결과는 `cachelist.json`으로 저장됩니다. (저장 위치: `%APPDATA%\Local\Programs\fclistLister`)

## 라이선스

MIT License. (c) 2026 Nova de Hi and KTUG.
