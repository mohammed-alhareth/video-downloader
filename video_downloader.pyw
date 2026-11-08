#! python3
"""
Video Downloader
----------------
small desktop app to download videos from a link (youtube, google drive, x,
tiktok ...) using yt-dlp. videos go to Videos/Video Downloader

made for learning purposes (python + tkinter + yt-dlp)
only download videos that you own or have permission to download
the author is not responsible for any misuse of this tool

first time: run install.bat
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

APP_ID = "VideoDownloader.App"
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
        root.title("Video Downloader")
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

        tk.Label(root, text=str(SAVE_DIR), font=("Segoe UI", 9), fg="gray", anchor=anchor).pack(fill="x", padx=16)

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
    App(root)
    root.mainloop()
