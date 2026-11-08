#! python3
"""
Video Downloader
----------------
Copyright (c) 2026 DOSAN

small desktop app to download videos from a link (youtube, google drive, x,
tiktok ...) using yt-dlp. videos go to Videos/Video Downloader

made for learning purposes (python + tkinter + yt-dlp)
only download videos that you own or have permission to download
the author is not responsible for any misuse of this tool

first time: run install.bat
the terms of use window shows every time the app starts (see TERMS.md)
"""

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk

APP_ID = "DOSAN.VideoDownloader"
AUTHOR = "DOSAN"
COPYRIGHT = "© 2026 DOSAN"
HERE = Path(__file__).resolve().parent
SAVE_DIR = Path.home() / "Videos" / "Video Downloader"
SETTINGS = Path(os.environ.get("APPDATA", Path.home())) / "VideoDownloader" / "settings.json"
MAX_ATTEMPTS = 10
WAIT_BETWEEN = 30  # sec
CREATE_NEW_CONSOLE = 0x00000010


# ===== texts (ar / en) =====
TEXT = {
    "ar": {
        "paste_label": "الصق رابط الفيديو",
        "paste": "لصق",
        "download": "تحميل",
        "open_folder": "فتح المجلد",
        "setup": "تجهيز البرنامج",
        "other_lang": "English",
        "need_ytdlp": "مكتبة التحميل مو مثبتة، اضغط تجهيز البرنامج",
        "no_ffmpeg": "برنامج ffmpeg مو مثبت، فما يقدر ينزل أعلى جودة",
        "no_ffmpeg2": "اضغط تجهيز البرنامج عشان يتثبت",
        "attempt": "المحاولة رقم {n}",
        "title": "اسم الفيديو",
        "quality": "أعلى جودة متوفرة",
        "reason": "سبب الخطأ",
        "err_js": "الموقع يحتاج تحديث، اضغط تجهيز البرنامج وبعدين افتح البرنامج من جديد",
        "err_unsupported": "هذا الموقع غير مدعوم، أو الرابط ما فيه فيديو",
        "err_login": "الفيديو خاص أو يحتاج تسجيل دخول، فما يقدر البرنامج يحمّله",
        "err_stop": "وقف التحميل، جرّب تضغط تجهيز البرنامج وتعيد",
        "retry": "مشكلة اتصال، بعيد المحاولة بعد {s} ثانية",
        "failed_all": "ما قدر يحمّل بعد كل المحاولات، جرّب شبكة ثانية",
        "success": "تم التحميل بنجاح ✅",
        "preparing": "جاري التحضير",
        "bad_url": "الصق رابط صحيح يبدأ بـ https",
        "part1": "الجزء الأول",
        "part2": "الجزء الثاني",
        "progress": "تحميل {part}   {pct:.0f}٪   السرعة {speed:.1f} ميجا بالثانية   باقي {mins} دقيقة",
        "merging": "جاري دمج الصورة والصوت",
        "setup_missing": "ملف setup.bat مو موجود جنب البرنامج",
        "setup_opened": "فتحت نافذة التجهيز، تابع التنزيل فيها",
        "setup_running": "جاري التجهيز في نافذة الـ Terminal",
        "setup_fail": "ما قدر يفتح نافذة التجهيز",
        "setup_done": "خلص التجهيز ✅  سكّر البرنامج وافتحه من جديد",
    },
    "en": {
        "paste_label": "Paste the video link",
        "paste": "Paste",
        "download": "Download",
        "open_folder": "Open folder",
        "setup": "Setup",
        "other_lang": "العربية",
        "need_ytdlp": "yt-dlp is not installed. Press Setup.",
        "no_ffmpeg": "ffmpeg is not installed, so the highest quality is not possible.",
        "no_ffmpeg2": "Press Setup to install it.",
        "attempt": "Attempt {n}",
        "title": "Video title",
        "quality": "Best available quality",
        "reason": "Error details",
        "err_js": "The site needs an update. Press Setup, then reopen the app.",
        "err_unsupported": "This site is not supported, or the link has no video.",
        "err_login": "The video is private or needs a login, so it can't be downloaded.",
        "err_stop": "Download stopped. Try Setup, then try again.",
        "retry": "Connection problem. Retrying in {s} seconds.",
        "failed_all": "Failed after all attempts. Try another network.",
        "success": "Downloaded successfully ✅",
        "preparing": "Preparing",
        "bad_url": "Paste a valid link that starts with https",
        "part1": "part 1",
        "part2": "part 2",
        "progress": "Downloading {part}   {pct:.0f}%   {speed:.1f} MB/s   {mins} min left",
        "merging": "Merging video and audio",
        "setup_missing": "setup.bat was not found next to the app.",
        "setup_opened": "Setup window opened. Follow the progress there.",
        "setup_running": "Setup is running in the terminal window",
        "setup_fail": "Could not open the setup window.",
        "setup_done": "Setup finished ✅  Close the app and open it again.",
    },
}


def load_lang():
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8")).get("lang", "ar")
    except (OSError, ValueError):
        return "ar"


def save_lang(lang):
    try:
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS.write_text(json.dumps({"lang": lang}), encoding="utf-8")
    except OSError:
        pass


# ===== terms of use =====
TERMS = {
    "en": {
        "title": "Terms of Use",
        "heading": "Please read these terms before using Video Downloader",
        "body": """Video Downloader ("the Software") is developed and owned by DOSAN ("the author").
By using the Software, you agree to the following terms:

1. Educational purpose
The Software is provided for educational and personal purposes only.

2. Your responsibility
You are solely and fully responsible for how you use the Software and for any content you download with it. You may only download content that you own, or that you have clear permission from the owner to download.

3. Prohibited use
You must not use the Software for any illegal or unethical purpose, including but not limited to: copyright infringement, piracy, re-uploading or selling other people's content, downloading private or restricted content without the owner's consent, bypassing access controls, or harming any person or organization.

4. Laws and website terms
You must follow the laws of your country and the terms of service of every website you download from.

5. No warranty
The Software is provided "as is", without warranty of any kind, express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, and non-infringement.

6. Limitation of liability
In no event shall the author or contributors be liable for any claim, damages, losses, legal action or other liability, whether in contract, tort or otherwise, arising from, out of, or in connection with the Software or its use or misuse.

7. Indemnification
You agree to defend, indemnify and hold harmless the author and contributors from and against any claims, damages, losses, fines, and legal costs (including lawyer fees) arising from your use of the Software or your violation of these terms or of any law or third-party right.

8. Third-party tools
The Software uses third-party tools (yt-dlp, FFmpeg, Deno), each under its own license. The author is not affiliated with these tools or with any website.

9. Acceptance
If you do not agree to these terms, do not use the Software. Pressing "I Agree" means you have read, understood and accepted all of the terms above.""",
        "check": "I have read and agree to the Terms of Use",
        "agree": "I Agree",
        "decline": "Decline",
        "other_lang": "العربية",
    },
    "ar": {
        "title": "شروط الاستخدام",
        "heading": "يرجى قراءة الشروط التالية قبل استخدام البرنامج",
        "body": """برنامج Video Downloader (ويُشار إليه بـ "البرنامج") من تطوير DOSAN وملكيته (ويُشار إليه بـ "صاحب البرنامج").
باستخدامك للبرنامج، فإنك توافق على الشروط التالية:

١. الغرض التعليمي
البرنامج مقدَّم لأغراض تعليمية وشخصية فقط.

٢. مسؤولية المستخدم
أنت وحدك المسؤول مسؤولية كاملة عن طريقة استخدامك للبرنامج، وعن أي محتوى تقوم بتحميله. ولا يجوز لك تحميل أي محتوى إلا إذا كان ملكاً لك، أو حصلت على إذن صريح من صاحبه.

٣. الاستخدام الممنوع
يُمنع استخدام البرنامج لأي غرض غير قانوني أو غير أخلاقي، ومن ذلك على سبيل المثال لا الحصر: انتهاك حقوق النشر، والقرصنة، وإعادة نشر محتوى الآخرين أو بيعه، وتحميل المحتوى الخاص أو المقيّد دون موافقة صاحبه، وتجاوز أنظمة الحماية، أو الإضرار بأي شخص أو جهة.

٤. الأنظمة وشروط المواقع
يجب عليك الالتزام بأنظمة وقوانين بلدك، وبشروط الاستخدام الخاصة بكل موقع تقوم بالتحميل منه.

٥. عدم الضمان
يُقدَّم البرنامج "كما هو" دون أي ضمان من أي نوع، صريحاً كان أو ضمنياً، بما في ذلك على سبيل المثال لا الحصر: ضمان صلاحيته للبيع، أو ملاءمته لغرض معين، أو عدم انتهاكه لحقوق الغير.

٦. حدود المسؤولية
لا يتحمّل صاحب البرنامج أو المساهمون فيه بأي حال من الأحوال أي مسؤولية عن أي مطالبة أو أضرار أو خسائر أو دعاوى قانونية أو أي التزام آخر، سواء كان تعاقدياً أو تقصيرياً أو غير ذلك، ينتج عن البرنامج أو عن استخدامه أو سوء استخدامه أو يتعلق به.

٧. التعويض
توافق على أن تدافع عن صاحب البرنامج والمساهمين فيه، وأن تعوّضهم وتُخلي مسؤوليتهم من أي مطالبات أو أضرار أو خسائر أو غرامات أو تكاليف قانونية (بما في ذلك أتعاب المحاماة) تنتج عن استخدامك للبرنامج، أو عن مخالفتك لهذه الشروط أو لأي نظام أو لأي حق من حقوق الغير.

٨. أدوات الطرف الثالث
يستخدم البرنامج أدوات خارجية (yt-dlp و FFmpeg و Deno)، ولكل أداة رخصتها الخاصة. وصاحب البرنامج ليس له أي علاقة بهذه الأدوات أو بأي موقع.

٩. الموافقة
إذا كنت لا توافق على هذه الشروط، فلا تستخدم البرنامج. والضغط على زر "أوافق" يعني أنك قرأت جميع الشروط أعلاه وفهمتها ووافقت عليها.""",
        "check": "قرأت شروط الاستخدام وأوافق عليها",
        "agree": "أوافق",
        "decline": "لا أوافق",
        "other_lang": "English",
    },
}


def ask_terms(root, lang):
    """shows the terms window. returns (accepted, lang)"""
    state = {"ok": False, "lang": lang}
    win = tk.Toplevel(root)
    win.geometry("620x560")
    win.resizable(False, False)
    win.protocol("WM_DELETE_WINDOW", win.destroy)  # closing the window = decline

    def draw():
        for w in win.winfo_children():
            w.destroy()
        L = state["lang"]
        tx = TERMS[L]
        rtl = L == "ar"
        near, far = ("right", "left") if rtl else ("left", "right")
        win.title(f'{tx["title"]} - {AUTHOR}')

        top = tk.Frame(win)
        top.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(top, text=tx["heading"], font=("Segoe UI", 11, "bold")).pack(side=near)
        tk.Button(top, text=tx["other_lang"], font=("Segoe UI", 9), width=9,
                  command=switch).pack(side=far)

        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True, padx=16)
        sb = tk.Scrollbar(frame)
        sb.pack(side="left" if rtl else "right", fill="y")
        box = tk.Text(frame, wrap="word", font=("Segoe UI", 10), yscrollcommand=sb.set,
                      padx=8, pady=6)
        box.tag_configure("dir", justify="right" if rtl else "left")
        box.insert("1.0", tx["body"], "dir")
        box.config(state="disabled")
        box.pack(side="left", fill="both", expand=True)
        sb.config(command=box.yview)

        var = tk.BooleanVar(value=False)
        tk.Checkbutton(win, text=tx["check"], variable=var, font=("Segoe UI", 10),
                       command=lambda: agree_btn.config(state="normal" if var.get() else "disabled")
                       ).pack(anchor="e" if rtl else "w", padx=16, pady=(8, 4))

        btns = tk.Frame(win)
        btns.pack(fill="x", padx=16, pady=(0, 14))
        agree_btn = tk.Button(btns, text=tx["agree"], font=("Segoe UI", 11, "bold"), width=12,
                              state="disabled", command=accept)
        agree_btn.pack(side=near)
        tk.Button(btns, text=tx["decline"], font=("Segoe UI", 11), width=12,
                  command=win.destroy).pack(side=near, padx=8)
        tk.Label(btns, text=COPYRIGHT, font=("Segoe UI", 9, "bold"), fg="gray").pack(side=far)

    def switch():
        state["lang"] = "en" if state["lang"] == "ar" else "ar"
        draw()

    def accept():
        state["ok"] = True
        win.destroy()

    draw()
    win.lift()
    win.focus_force()
    try:
        win.wait_visibility()
        win.grab_set()
    except tk.TclError:
        pass
    root.wait_window(win)
    return state["ok"], state["lang"]


# ===== helpers =====
def refresh_path():
    # after installing ffmpeg/deno the PATH of this process is old, so read it again
    parts = os.environ.get("PATH", "").split(os.pathsep)
    if os.name == "nt":
        import winreg
        for root, key in ((winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                          (winreg.HKEY_CURRENT_USER, r"Environment")):
            try:
                with winreg.OpenKey(root, key) as k:
                    val, _ = winreg.QueryValueEx(k, "Path")
                    parts += os.path.expandvars(val).split(os.pathsep)
            except OSError:
                pass
        parts.append(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links"))
        parts.append(os.path.expandvars(r"%USERPROFILE%\.deno\bin"))
    seen, clean = set(), []
    for p in parts:
        if p and p.lower() not in seen:
            seen.add(p.lower())
            clean.append(p)
    os.environ["PATH"] = os.pathsep.join(clean)


def python_exe():
    # need python.exe not pythonw.exe to run pip
    exe = Path(sys.executable)
    alt = exe.with_name("python.exe")
    return str(alt if alt.exists() else exe)


def set_taskbar_identity():
    # without this windows shows the python icon in the taskbar
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except (AttributeError, OSError):
            pass


# ===== download =====
NETWORK_WORDS = ("timed out", "timeout", "connection", "10054", "reset", "temporar",
                 "http error 5", "remote end closed", "ssl", "read error")
LOGIN_WORDS = ("login", "log in", "sign in", "cookies", "private video", "age-restricted", "confirm your age", "members")
JS_WORDS = ("javascript", "js runtime", "deno", "challenge", "n challenge", "signature")


def has(msg, words):
    m = msg.lower()
    return any(w in m for w in words)


def clean_title(title: str) -> str:
    title = re.sub(r"\.(mp4|mkv|mov|webm|m4v|avi)$", "", title.strip(), flags=re.I)
    title = re.sub(r'[<>:"/\\|?*\n\r\t]', "_", title)
    return title[:150].strip() or "video"


class Downloader:
    def __init__(self, ui):
        self.ui = ui
        self.t = ui.t
        self.part = 0

    def hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes", 0)
            pct = done / total * 100 if total else 0
            speed = (d.get("speed") or 0) / 1024 / 1024
            mins = (d.get("eta") or 0) // 60
            part = self.t("part1") if self.part == 0 else self.t("part2")
            self.ui.progress(pct, self.t("progress", part=part, pct=pct, speed=speed, mins=mins))
        elif d["status"] == "finished":
            self.part += 1

    def pp_hook(self, d):
        if d["postprocessor"] in ("Merger", "FFmpegMerger") and d["status"] == "started":
            self.ui.progress(100, self.t("merging"))

    def run(self, url):
        import yt_dlp

        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        has_ffmpeg = shutil.which("ffmpeg") is not None
        if not has_ffmpeg:
            self.ui.log(self.t("no_ffmpeg"))
            self.ui.log(self.t("no_ffmpeg2"))

        base = {
            # best video + best audio (needs ffmpeg to merge)
            "format": "bv*+ba/b" if has_ffmpeg else "b",
            # sort by resolution first then fps
            "format_sort": ["res", "fps", "hdr:12", "vbr", "abr", "asr"],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,  # dont download whole playlist
            "socket_timeout": 60,
            "extractor_retries": 10,
        }
        opts = {
            **base,
            "merge_output_format": "mp4",
            "retries": 30,
            "fragment_retries": 30,
            "continuedl": True,
            "noprogress": True,
            "progress_hooks": [self.hook],
            "postprocessor_hooks": [self.pp_hook],
        }

        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.part = 0
            try:
                self.ui.log(self.t("attempt", n=attempt))
                with yt_dlp.YoutubeDL(base) as ydl:
                    info = ydl.extract_info(url, download=False)
                title = clean_title(info.get("title") or info.get("id") or "video")
                site = info.get("extractor_key") or ""
                self.ui.log(self.t("title"))
                self.ui.log(f"{title}   [{site}]", ltr=True)

                h, fps = info.get("height"), info.get("fps")
                vcodec = (info.get("vcodec") or "").split(".")[0]
                q = f"{h}p" if h else (info.get("resolution") or "")
                if fps:
                    q += f"  {round(fps)}fps"
                if vcodec and vcodec != "none":
                    q += f"  {vcodec}"
                self.ui.log(self.t("quality"))
                self.ui.log(q.strip() or "unknown", ltr=True)

                opts["outtmpl"] = str(SAVE_DIR / (title.replace("%", "%%") + ".%(ext)s"))
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                self.ui.done(True, self.t("success"))
                return

            except Exception as e:
                reason = str(e).replace("ERROR: ", "").strip()
                self.ui.log(self.t("reason"))
                self.ui.log(reason[:400], ltr=True, error=True)

                if has(reason, JS_WORDS):
                    self.ui.done(False, self.t("err_js"))
                    return
                if has(reason, ("unsupported url",)):
                    self.ui.done(False, self.t("err_unsupported"))
                    return
                if has(reason, LOGIN_WORDS):
                    self.ui.done(False, self.t("err_login"))
                    return
                if not has(reason, NETWORK_WORDS):
                    self.ui.done(False, self.t("err_stop"))
                    return
                self.ui.log(self.t("retry", s=WAIT_BETWEEN))
                time.sleep(WAIT_BETWEEN)

        self.ui.done(False, self.t("failed_all"))


# ===== setup =====
def setup(ui):
    # opens cmd window with setup.bat and waits
    t = ui.t
    bat = HERE / "setup.bat"
    if not bat.exists():
        ui.done(False, t("setup_missing"))
        return
    ui.log(t("setup_opened"))
    ui.progress(0, t("setup_running"))
    try:
        p = subprocess.Popen([str(bat), python_exe()], cwd=str(HERE),
                             creationflags=CREATE_NEW_CONSOLE)
        p.wait()
    except OSError as e:
        ui.log(str(e), ltr=True, error=True)
        ui.done(False, t("setup_fail"))
        return
    refresh_path()
    ui.progress(100, "")
    ui.done(True, t("setup_done"))


# ===== GUI =====
class App:
    def __init__(self, root):
        self.root = root
        self.lang = load_lang()
        self.busy = False
        root.title(f"Video Downloader - {AUTHOR}")
        root.geometry("660x430")
        root.resizable(False, False)
        self.set_icon()
        refresh_path()
        self.build()

        try:
            import yt_dlp  # noqa: F401
        except ImportError:
            self.log(self.t("need_ytdlp"))
            self.btn.config(state="disabled")

    # ----- language -----
    def t(self, key, **kw):
        text = TEXT[self.lang][key]
        return text.format(**kw) if kw else text

    @property
    def rtl(self):
        return self.lang == "ar"

    def switch_lang(self):
        if self.busy:
            return
        self.lang = "en" if self.lang == "ar" else "ar"
        save_lang(self.lang)
        url = self.url.get()
        for w in self.root.winfo_children():
            w.destroy()
        self.build()
        self.url.insert(0, url)

    # ----- icon -----
    def set_icon(self):
        ico = HERE / "icon.ico"
        png = HERE / "icon.png"
        try:
            if ico.exists():
                self.root.iconbitmap(default=str(ico))
            if png.exists():
                self._icon_img = tk.PhotoImage(file=str(png))
                self.root.iconphoto(True, self._icon_img)  # bigger icon for taskbar
        except tk.TclError:
            pass

    # ----- layout -----
    def build(self):
        root = self.root
        font = ("Segoe UI", 11)
        anchor = "e" if self.rtl else "w"
        near, far = ("right", "left") if self.rtl else ("left", "right")

        top = tk.Frame(root)
        top.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(top, text=self.t("paste_label"), font=font).pack(side=near)
        tk.Button(top, text=self.t("other_lang"), font=("Segoe UI", 9), width=9,
                  command=self.switch_lang).pack(side=far)

        row = tk.Frame(root)
        row.pack(fill="x", padx=16)
        tk.Button(row, text=self.t("paste"), font=font, width=8, command=self.paste).pack(side=far, padx=(0, 6) if self.rtl else (6, 0))
        self.url = tk.Entry(row, font=("Segoe UI", 10), justify="left")
        self.url.pack(side=near, fill="x", expand=True, ipady=4)
        self.url.bind("<Return>", lambda e: self.start())

        btns = tk.Frame(root)
        btns.pack(fill="x", padx=16, pady=12)
        self.btn = tk.Button(btns, text=self.t("download"), font=("Segoe UI", 12, "bold"), width=12, command=self.start)
        self.btn.pack(side=near)
        tk.Button(btns, text=self.t("open_folder"), font=font, width=12, command=self.open_folder).pack(side=near, padx=8)
        self.setup_btn = tk.Button(btns, text=self.t("setup"), font=font, width=14, command=self.run_setup)
        self.setup_btn.pack(side=far)

        self.bar = ttk.Progressbar(root, length=628, maximum=100)
        self.bar.pack(padx=16)
        self.status = tk.Label(root, text="", font=("Segoe UI", 10), anchor=anchor)
        self.status.pack(fill="x", padx=16, pady=(4, 6))

        self.box = tk.Text(root, height=9, font=("Segoe UI", 10), state="disabled")
        self.box.tag_configure("r", justify="right")
        self.box.tag_configure("l", justify="left")
        self.box.tag_configure("err", justify="left", foreground="#a00")
        self.box.pack(fill="both", padx=16, pady=(0, 6))

        foot = tk.Frame(root)
        foot.pack(fill="x", padx=16)
        tk.Label(foot, text=str(SAVE_DIR), font=("Segoe UI", 9), fg="gray").pack(side=near)
        tk.Label(foot, text=COPYRIGHT, font=("Segoe UI", 9, "bold"), fg="gray").pack(side=far)

    # tkinter is not thread safe so use after()
    def _ui(self, fn):
        self.root.after(0, fn)

    def log(self, text, ltr=False, error=False):
        tag = "err" if error else ("l" if (ltr or not self.rtl) else "r")

        def f():
            self.box.config(state="normal")
            self.box.insert("end", text + "\n", tag)
            self.box.see("end")
            self.box.config(state="disabled")
        self._ui(f)

    def progress(self, pct, text):
        self._ui(lambda: (self.bar.config(value=pct), self.status.config(text=text, fg="black")))

    def done(self, ok, text):
        def f():
            self.busy = False
            self.status.config(text=text, fg="green" if ok else "red")
            self.btn.config(state="normal")
            self.setup_btn.config(state="normal")
            self.log(text)
        self._ui(f)

    # ----- actions -----
    def paste(self):
        try:
            self.url.delete(0, "end")
            self.url.insert(0, self.root.clipboard_get().strip())
        except tk.TclError:
            pass

    def open_folder(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(SAVE_DIR)

    def lock(self):
        self.busy = True
        self.btn.config(state="disabled")
        self.setup_btn.config(state="disabled")

    def start(self):
        url = self.url.get().strip()
        if not re.match(r"https?://", url):
            self.status.config(text=self.t("bad_url"), fg="red")
            return
        self.lock()
        self.bar.config(value=0)
        self.status.config(text=self.t("preparing"), fg="black")
        threading.Thread(target=Downloader(self).run, args=(url,), daemon=True).start()

    def run_setup(self):
        self.lock()
        threading.Thread(target=setup, args=(self,), daemon=True).start()


if __name__ == "__main__":
    set_taskbar_identity()  # has to be before tk.Tk()
    root = tk.Tk()
    root.withdraw()  # hide main window until terms are accepted
    for f in ("icon.ico",):
        if (HERE / f).exists():
            try:
                root.iconbitmap(default=str(HERE / f))
            except tk.TclError:
                pass

    accepted, lang = ask_terms(root, load_lang())
    if not accepted:
        root.destroy()
        sys.exit(0)

    save_lang(lang)
    root.deiconify()
    App(root)
    root.mainloop()
