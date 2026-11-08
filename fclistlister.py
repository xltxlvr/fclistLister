###
### version 2.0
###
import subprocess, os, json
import tkinter as tk

from tkinter import ttk, messagebox
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, ImageTk
import re
import platform

# APPDATA 기반 경로 설정
APPDATA = os.environ.get("APPDATA")
CACHE_DIR = os.path.join(APPDATA, "Local", "Programs", "fclistLister")
CACHE_FILE = os.path.join(CACHE_DIR, "cachelist.json")

# 디렉토리 없으면 생성
os.makedirs(CACHE_DIR, exist_ok=True)

def save_fonts(fonts):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(fonts, f, ensure_ascii=False)

def load_cached_fonts():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_font_info_with_fonttools(path):
    """otfinfo -i 및 -s 기능을 fontTools로 구현"""
    try:
        font = TTFont(path, fontNumber=0)

        # 1. 'name' 테이블 정보
        info_list = []
        name_table = font['name']
        target_ids = [0, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14]
        for record in name_table.names:
            if record.nameID in target_ids:
                try:
                    val = record.toUnicode()
                    info_list.append(f"Name ID {record.nameID}: {val}")
                except:
                    continue
        info_output = "\n".join(sorted(set(info_list)))

        # 2. GSUB/GPOS Feature + Script 정보
        features = set()
        scripts = {}
        for tag in ['GSUB', 'GPOS']:
            if tag in font:
                table = font[tag].table
                # FeatureList
                if table.FeatureList:
                    for record in table.FeatureList.FeatureRecord:
                        features.add(record.FeatureTag)
                # ScriptList
                if table.ScriptList:
                    for script_record in table.ScriptList.ScriptRecord:
                        script_tag = script_record.ScriptTag
                        lang_tags = []
                        # 기본(DefaultLangSys)
                        if script_record.Script.DefaultLangSys:
                            lang_tags.append("dflt")
                        # 추가 LangSys
                        for lang_record in script_record.Script.LangSysRecord:
                            lang_tags.append(lang_record.LangSysTag)
                        scripts[script_tag] = lang_tags

        subs_output = ", ".join(sorted(features)) if features else "No layout features found."
        scripts_output = "\n".join(
            f"{script}: {', '.join(langs)}" for script, langs in scripts.items()
        ) if scripts else "No scripts found."

        font.close()
        return info_output, subs_output, scripts_output

    except Exception as e:
        return None, None, f"Error: {str(e)}"

def show_otfinfo():
    selected = tree.selection()
    if not selected:
        return
    item = tree.item(selected[0])
    filename = item["values"][2]

    path = font_path_map.get(filename)
    if not path:
        messagebox.showerror("Error", f"경로를 찾을 수 없습니다: {filename}")
        return

    # fontTools를 사용하여 정보 가져오기
    output_info, output_subs, output_scripts = get_font_info_with_fonttools(path)
    
    if output_info is None:
        messagebox.showerror("Error", f"폰트 분석 실패: {output_subs}")
        return

    # 팝업 창 생성 (기존 UI 코드와 동일)
    popup = tk.Toplevel(root)
    popup.title(f"Font Analysis (fontTools) - {filename}")
        
    # 위쪽: -i 결과
    frame_info = tk.LabelFrame(popup, text="Name Table")
    frame_info.pack(expand=True, fill="both", padx=5, pady=5)
    
    text_info = tk.Text(frame_info, wrap="word", width=80, height=12)
    text_info.insert("1.0", output_info if output_info else "출력 없음")
    text_info.config(state="disabled")
    text_info.pack(expand=True, fill="both")
    
    # 아래쪽: -s 결과
    frame_subs = tk.LabelFrame(popup, text="GSUB/GPOS features and Scrips")
    frame_subs.pack(expand=True, fill="both", padx=5, pady=5)
    
    text_subs = tk.Text(frame_subs, wrap="word", width=80, height=12)

    # 두 개를 줄바꿈으로 연결
    subs_text = (output_subs if output_subs else "출력 없음") + "\n" + \
                (output_scripts if output_scripts else "출력 없음")

    text_subs.insert("1.0", subs_text)

    text_subs.config(state="disabled")
    text_subs.pack(expand=True, fill="both")


def open_file_location():
    selected_item = tree.selection()
    if not selected_item:
        return
    
    values = tree.item(selected_item[0], "values")
    filename = values[2]
    full_path = font_path_map.get(filename)
    
    if not full_path:
        messagebox.showwarning("경고", "파일 경로 정보를 찾을 수 없습니다.")
        return

    # 경로 정규화 및 대소문자 구분 방지용 소문자 변환
    norm_path = os.path.normpath(full_path)
    lower_path = norm_path.lower()
    
    # 윈도우 시스템 폰트 폴더 경로 정의
    win_fonts_dir = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts').lower()

    try:
        if platform.system() == "Windows":
            if win_fonts_dir in lower_path:
                # 시스템 폰트 폴더인 경우 알림창만 띄움
                messagebox.showinfo("안내", 
                    f"해당 폰트 파일은 Windows 시스템 글꼴 공간에 있습니다.\n\n경로: {norm_path}\n\n시스템 보안 정책상 해당 폴더를 직접 열 수 없습니다.")
            else:
                # 사용자 설치 폰트(%LocalAppData% 등)는 정상적으로 열기 시도
                if os.path.exists(norm_path):
                    subprocess.run(['explorer', '/select,', norm_path])
                else:
                    messagebox.showerror("오류", "파일이 실제 경로에 존재하지 않습니다.")
        else:
            # macOS/Linux (기존 로직 유지)
            path = os.path.dirname(norm_path)
            cmd = ["open", path] if platform.system() == "Darwin" else ["xdg-open", path]
            subprocess.run(cmd)
            
    except Exception as e:
        messagebox.showerror("오류", f"작업 중 오류 발생: {e}")

def check_texlive():
    try:
        # 1. kpsewhich를 이용해 현재 TeX 실행 파일들이 위치한 경로(SELFAUTOLOC)를 가져옵니다.
        # 이 경로는 보통 .../bin/windows 또는 .../bin/x86_64-linux 형태입니다.
        result = subprocess.run(
            ["kpsewhich", "-var-value=SELFAUTOLOC"], 
            capture_output=True, text=True, check=True
        )
        bin_path = result.stdout.strip()
        
        if not bin_path:
            return False

        # 2. OS에 따른 tlmgr 파일명 설정
        tlmgr_name = "tlmgr.bat" if platform.system() == "Windows" else "tlmgr"
        
        # 3. 해당 경로에 tlmgr 파일이 물리적으로 존재하는지 확인
        return os.path.exists(os.path.join(bin_path, tlmgr_name))

    except (subprocess.CalledProcessError, FileNotFoundError):
        # kpsewhich 명령어가 없거나 실행 중 오류가 나면 TeX 환경 자체가 없거나 MiKTeX일 가능성이 높음
        return False

def check_miktex():
    try:
        subprocess.run(["initexmf", "--version"], capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# def check_miktex():
#     try:
#         # MiKTeX은 pdflatex --version 결과에 이름이 명시됩니다.
#         result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True)
#         return "MiKTeX" in result.stdout
#     except:
#         return False

def update_fonts():
    # MiKTeX/TeXLive 설치 체크 (기존 함수 활용)
    if check_miktex():
        messagebox.showinfo("Info", "MiKTeX이 설치되어 있습니다. (별도 설정 불필요)")
        return
    if not check_texlive():
        messagebox.showwarning("Warning", "TeXLive가 설치되어 있지 않습니다.")
        return

    try:
        # 1. TEXMFSYSVAR 경로 및 fc-cache 위치 확인
        # kpsewhich를 사용해 시스템 변수와 실행 파일 경로를 동적으로 가져옵니다.
        result = subprocess.run(["kpsewhich", "-var-value=TEXMFSYSVAR"], 
                                capture_output=True, text=True, check=True)
        mydirvar = result.stdout.strip()
        
        # 2. local.conf 설정 파일 생성
        conf_dir = os.path.join(mydirvar, "fonts", "conf")
        os.makedirs(conf_dir, exist_ok=True)

        local_fonts_dir = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows", "Fonts")
        # XML 형식을 명확히 지켜 작성합니다.
        local_conf_content = f'<?xml version="1.0"?>\n<fontconfig>\n  <dir>{local_fonts_dir}</dir>\n</fontconfig>'
        
        conf_file_path = os.path.join(conf_dir, "local.conf")
        with open(conf_file_path, "w", encoding="utf-8") as f:
            f.write(local_conf_content)

        # 3. fc-cache 실행 및 종료 코드 확인
        # fc-cache의 경로를 직접 지정하는 대신 시스템 환경변수에 있는 것을 우선 사용 시도
        # 만약 실패하면 상세 종료 코드를 캡처합니다.
        try:
            # -f(force), -v(verbose), -s(system-only 아님) 옵션 검토 필요
            refresh_process = subprocess.run(["fc-cache", "-f", "-v"], 
                                           capture_output=True, text=True, check=True)
            print(f"fc-cache Output: {refresh_process.stdout}")
        except subprocess.CalledProcessError as e:
            # 0이 아닌 종료 코드가 반환되었을 때 여기에서 캡처됩니다.
            raise Exception(f"fc-cache 실행 실패 (종료 코드: {e.returncode})\n상세: {e.stderr}")

        messagebox.showinfo("Success", "폰트 설정 및 캐시 갱신이 완료되었습니다.")

    except PermissionError:
        messagebox.showwarning("Permission Required", "관리자 권한으로 프로그램을 실행해 주세요.")
    except Exception as e:
        messagebox.showerror("Error", f"작업 중 오류 발생:\n{str(e)}")

# 원본 데이터 저장용
font_data = []
font_path_map = {}


def load_fonts():
    global font_data, font_path_map
    font_data = []
    font_path_map = {}
    
    # 트리뷰 초기화
    for item in tree.get_children():
        tree.delete(item)

    # 허용할 확장자 리스트 (소문자 기준)
    valid_extensions = {'.ttf', '.otf', '.ttc', '.otc'}
    
    # 상태 업데이트: 시작 메시지
    status_var.set("폰트 목록을 불러오는 중...")
    root.update_idletasks() # UI 즉시 갱신

    try:
        # kpsewhich로 fc-list 경로 찾기
        result = subprocess.run(["kpsewhich", "-var-value=SELFAUTOLOC"], capture_output=True, text=True, check=True)
        fc_list_path = os.path.join(result.stdout.strip(), "fc-list")

        # fc-list 실행
        result = subprocess.run(
            [fc_list_path, ":", "--format=%{file}|%{family}|%{style}\n"],
            capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        
        for line in result.stdout.strip().split("\n"):
            if not line.strip(): continue
            parts = line.split("|")
            if len(parts) < 3: continue
            
            path, families, styles = parts[0].strip(), parts[1].strip(), parts[2].strip()
            
            # --- 확장자 필터링 ---
            filename = os.path.basename(path)
            ext = os.path.splitext(filename)[1].lower()
            
            if ext not in valid_extensions:
                continue # 허용되지 않은 확장자는 제외
            # --------------------
            
            main_family = families.split(",")[0].strip()
            main_style = styles.split(",")[0].strip() if styles else ""
            
            if main_style and main_style.lower() != "regular":
                fontspec_name = f"{main_family} {main_style}"
            else:
                fontspec_name = main_family
            
            other_names = ", ".join(families.split(",")[1:])

            # 데이터 저장 및 트리뷰 추가
            tree.insert("", "end", values=(fontspec_name, other_names, filename))
            font_data.append((fontspec_name, other_names, filename))
            font_path_map[filename] = path
        
        # --- 최종 개수 표시 ---
        total_count = len(font_data)
        status_var.set(f"총 {total_count}개의 유효한 폰트 파일이 있습니다.")
        # --------------------

        save_fonts(font_data)
            
    except Exception as e:
        status_var.set(f"오류 발생: {e}")
        messagebox.showerror("Error", f"fc-list 실행 실패: {e}")

def run_fc_cache():
    try:
        # TeXLive bin 디렉토리 위치 얻기
        result = subprocess.run(
            ["kpsewhich", "-var-value=SELFAUTOLOC"],
            capture_output=True, text=True, check=True
        )
        tex_bin_dir = result.stdout.strip()
        fc_cache_path = os.path.join(tex_bin_dir, "fc-cache")

        # fc-cache -frv 실행
        subprocess.run([fc_cache_path, "-frv"], check=True)
        messagebox.showinfo("Success", "fc-cache -frv 실행 완료")
    except Exception as e:
        messagebox.showerror("Error", f"fc-cache 실행 실패: {e}")

def show_status(message, duration=2000):
    """하단 바에 메시지를 표시하고 지정된 시간(ms) 후 초기화"""
    status_var.set(message)
    # duration(2초) 후에 다시 "준비 완료"로 변경
    root.after(duration, lambda: status_var.set("..."))

def copy_font_name():
    selected = tree.selection()
    if not selected:
        return
    item = tree.item(selected[0])
    font_name = item["values"][0]
    root.clipboard_clear()
    root.clipboard_append(font_name)
    # messagebox.showinfo("Copied", f"'{font_name}' 이름이 클립보드에 복사되었습니다.")
    # 알림창 대신 윈도우 하단이나 제목 표시줄에 살짝 표시 (예시)
    # root.title(f"{font_name} 복사됨")
    show_status(f" {font_name} 복사됨 ")

def copy_file_name():
    selected = tree.selection()
    if not selected:
        return
    item = tree.item(selected[0])
    file_name = item["values"][2]
    root.clipboard_clear()
    root.clipboard_append(file_name)
    # messagebox.showinfo("Copied", f"'{file_name}' 파일명이 클립보드에 복사되었습니다.")
    # root.title(f"{file_name} 복사됨")
    show_status(f" {file_name} 복사됨 ")

def show_context_menu(event):
    selected = tree.identify_row(event.y)
    if selected:
        tree.selection_set(selected)
        context_menu.post(event.x_root, event.y_root)

def show_info():
    info_text = (
        "Fontconfig-list Lister\n\n"
        "(c) 2026 Nova de Hi and KTUG, v2.0\n"
        "MIT license. Free.\n"
        "With Python3.13 and tkinter(Tcl/Tk)\n\n"
        "fc-list를 통해 설치된 폰트 목록을 보여주고, 선택한 폰트 이름\n"
        "또는 파일 이름을 클립보드에 복사하는 것입니다.\n"
        "목록 불러오기 후 [우클릭] 하세요.\n\n"
        "TeXLive 환경에서 local.conf를 업데이트하여\n"
        "Windows 사용자 폰트를 XeTeX이 인식하도록 설정합니다.\n\n"
        "local.conf 업데이트가 권한 문제로 실패하면\n"
        "관리자 권한으로 다시 시도하십시오.\n\n"
        "폰트 미리보기는 TTC/OTC에 적용되지 않습니다.\n\n"
        "F3: fc-list, Ctrl+F: 찾기, Ctrl+Enter: 폰트 이름 복사,\n"
        "Alt+Enter: 파일 이름 복사, Ctrl+I: 폰트 정보 보기\n"
    )
    messagebox.showinfo("프로그램 정보", info_text)

def sort_column(col, reverse):
    data = [(tree.set(k, col), k) for k in tree.get_children()]
    data.sort(reverse=reverse)
    for index, (val, k) in enumerate(data):
        tree.move(k, '', index)
    sort_reverse[col] = not reverse

def search_fonts():
    keyword = search_entry.get().strip().lower()
    for item in tree.get_children():
        tree.delete(item)
    if not keyword:
        for row in font_data:
            tree.insert("", "end", values=row)
        return
    for row in font_data:
        if (keyword in row[0].lower() or
            keyword in row[1].lower() or
            keyword in row[2].lower()):
            tree.insert("", "end", values=row)

# 글리프 기반 미리보기
def get_supported_chars(font_path):
    try:
        font = TTFont(font_path)
        cmap = font['cmap'].getBestCmap()
        supported = set(cmap.keys())
        return supported
    except Exception:
        return set()

def generate_sample_text(supported):
    samples = []
    alphabet = "The quick brown fox jumps over the lazy dog."
    if any(ord(c) in supported for c in alphabet):
        samples.append(alphabet)

    punct = "!?.,;:-()"
    if any(ord(c) in supported for c in punct):
        samples.append(punct)

    hangul = "저녁 교회 종소리 노을에 퍼지고"
    if any(ord(c) in supported for c in hangul):
        samples.append(hangul)

    hanja_traditional = "學而時習之 不亦說乎"
    if any(ord(c) in supported for c in hanja_traditional):
        samples.append("" + hanja_traditional)

    hanja_simplified = "学而时习之 不亦说乎"
    if any(ord(c) in supported for c in hanja_simplified):
        samples.append("" + hanja_simplified)

    # 일본어: 히라가나 + 카타카나
    japanese_hiragana = "こんにちは"
    japanese_katakana = "コンバンハ"
    if any(ord(c) in supported for c in japanese_hiragana + japanese_katakana):
        samples.append(japanese_hiragana + " " + japanese_katakana)

    return "\n".join(samples)

def show_preview(event):
    selected = tree.selection()
    if not selected:
        return
    item = tree.item(selected[0])
    font_name = item["values"][0]
    file_name = item["values"][2]
    font_path = font_path_map.get(file_name)
    if font_path:
        supported = get_supported_chars(font_path)
        sample_text = generate_sample_text(supported)

        # 폰트 로드
        try:
            font = ImageFont.truetype(font_path, 20)
        except Exception:
            font = ImageFont.load_default()

        # 임시 캔버스에서 텍스트 크기 계산
        dummy_img = Image.new("RGB", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        bbox = dummy_draw.textbbox((0, 0), sample_text, font=font)

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 여유 공간을 조금 더 추가
        img_width = text_width + 20
        img_height = text_height + 20

        # 실제 이미지 생성
        img = Image.new("RGB", (img_width, img_height), "white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), sample_text, font=font, fill="black")

        # Tkinter에 표시
        tk_img = ImageTk.PhotoImage(img)
        preview_label.config(image=tk_img)
        preview_label.image = tk_img  # 참조 유지


root = tk.Tk()
root.title("Fc-list 리스터")
root.geometry("800x600")

# --- 1. 통합 상단 툴바 (기존 유지) ---
top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

search_entry = tk.Entry(top_frame, width=25)
search_entry.pack(side=tk.LEFT, padx=(0, 5))
search_entry.bind("<Return>", lambda event: search_fonts())

tk.Button(top_frame, text="검색", command=search_fonts).pack(side=tk.LEFT, padx=(0, 15))
tk.Button(top_frame, text="fc-list (F3)", command=load_fonts).pack(side=tk.LEFT, padx=3)
tk.Button(top_frame, text="fc-cache", command=run_fc_cache).pack(side=tk.LEFT, padx=3)
tk.Button(top_frame, text="local.conf", command=update_fonts).pack(side=tk.LEFT, padx=3)
tk.Button(top_frame, text="About (F1)", command=show_info).pack(side=tk.RIGHT, padx=5)

# 상단 구분선
ttk.Separator(root, orient='horizontal').pack(fill='x')

# --- 2. 메인 PanedWindow (수직 조절 가능 구역) ---
# orient=tk.VERTICAL로 설정하여 위(리스트)와 아래(미리보기)를 나눕니다.
# sashrelief를 주면 구분선이 시각적으로 더 잘 보입니다.
paned_window = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief='raised', sashwidth=4)
paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# --- [상단 칸] 트리뷰 영역 ---
tree_frame = tk.Frame(paned_window)
# paned_window.add()를 통해 위젯을 추가합니다. weight=3은 리스트가 더 넓게 시작함을 의미합니다.
paned_window.add(tree_frame, minsize=200, height=400) 

columns = ("폰트 이름", "다른 이름", "파일 이름")
tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 트리뷰 컬럼 설정
sort_reverse = {col: False for col in columns}
for col in columns:
    tree.heading(col, text=col, command=lambda c=col: sort_column(c, sort_reverse[c]))
    tree.column(col, width=200 if col == "파일 이름" else 150, anchor="w")

# --- [하단 칸] 동적 미리보기 영역 ---
# minsize를 지정하여 너무 작아지지 않게 방어할 수 있습니다.
preview_frame = tk.Frame(paned_window, bg="white")
paned_window.add(preview_frame, minsize=100)

preview_label = tk.Label(preview_frame, bg="white", text="선택된 폰트 미리보기가 여기에 표시됩니다.")
preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# --- 3. 상태 표시줄 (최하단 고정) ---
status_var = tk.StringVar(value="대기 중...")
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief="sunken", anchor="w")
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

# --- 4. 메뉴 및 바인딩 ---
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="폰트 이름 복사 (Ctrl+Enter)", command=copy_font_name)
context_menu.add_command(label="파일 이름 복사 (Alt+Enter)", command=copy_file_name)
context_menu.add_command(label="폰트 정보 보기 (Ctrl+I)", command=show_otfinfo)
context_menu.add_command(label="파일 위치로 열기", command=open_file_location)

tree.bind("<Button-3>", show_context_menu)
tree.bind("<<TreeviewSelect>>", show_preview)

# 키바인딩
root.bind("<F1>", lambda e: show_info())
root.bind("<F3>", lambda e: load_fonts())
root.bind("<Control-f>", lambda e: search_entry.focus_set())

def go_first(event=None):
    children = tree.get_children()
    if children:
        tree.selection_set(children[0])
        tree.see(children[0])

def go_last(event=None):
    children = tree.get_children()
    if children:
        tree.selection_set(children[-1])
        tree.see(children[-1])

root.bind("<Control-Home>", go_first)
root.bind("<Control-End>", go_last)

root.bind("<Control-Return>", lambda event: copy_font_name())
root.bind("<Alt-Return>", lambda event: copy_file_name())
root.bind("<Control-i>", lambda event: show_otfinfo())

# load_cached_fonts()
load_fonts()

root.mainloop()
