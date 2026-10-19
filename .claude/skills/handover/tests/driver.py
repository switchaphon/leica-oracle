#!/usr/bin/env python3
"""Throwaway end-to-end tests for the /handover skill.

usage: driver.py <run_dir> <skill_src|-> <scenario,...>
  skill_src '-'  -> baseline: invoke the personal /handover (v1 command), no project skill
  scenarios      -> B0 (baseline layout), T1/T1b (oracle repo, T1 incl. T4 re-run), T2 (ψ symlink), T3 (no ψ),
                    T5 (long phrase), T6 (Thai session), T7/T8 (public/private GitHub origin, extra unpushed commit)
"""
import concurrent.futures as cf, glob, json, os, re, subprocess, sys, time, uuid

NCLAUDE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nclaude.sh")
RUN, SKILL_SRC, SCENS = sys.argv[1], (None if sys.argv[2] == "-" else sys.argv[2]), sys.argv[3].split(",")
INVOKE = "/handover" if SKILL_SRC is None else "/handover-next"
PSI = "ψ"

ORACLE_MD = "# Test Oracle\n\n**I am**: Test Oracle, a throwaway oracle used to test the handover skill.\n"
WORK_ORACLE = (
    "You are working in this repo on TASK-42 (add greetings). Do exactly these two things now, nothing else:\n"
    "1. Create src/greet.txt containing the single line `hello`, then commit only that file with the message `feat(TASK-42): add greeting`.\n"
    f"2. Write a short learning note to {PSI}/memory/learnings/2026-10-17_greeting-lowercase.md saying greetings must stay lowercase. Leave committing it to the end of the session.\n"
    "For later sessions (do NOT do these now): step 2 is to add src/farewell.txt containing `bye`; step 3 is to update README.md to list both files.\n"
    "Decision already agreed with the user: greeting files stay plain text, never JSON.")
WORK_ORACLE_TH = (
    "เรากำลังทำ TASK-42 (เพิ่มคำทักทาย) ใน repo นี้ ตอนนี้ทำแค่ 2 อย่างนี้ ห้ามทำอย่างอื่น:\n"
    "1. สร้าง src/greet.txt ที่มีบรรทัดเดียวว่า `hello` แล้ว commit เฉพาะไฟล์นั้นด้วยข้อความ `feat(TASK-42): add greeting`\n"
    f"2. เขียนโน้ตสั้น ๆ ที่ {PSI}/memory/learnings/2026-10-17_greeting-lowercase.md ว่าคำทักทายต้องเป็นตัวพิมพ์เล็กเสมอ ยังไม่ต้อง commit ไว้ commit ตอนจบ session\n"
    "งานรอบหน้า (ตอนนี้ยังไม่ต้องทำ): ขั้นที่ 2 เพิ่ม src/farewell.txt ที่มีคำว่า `bye` ขั้นที่ 3 อัปเดต README.md ให้มีทั้งสองไฟล์\n"
    "ตกลงกับผู้ใช้แล้วว่าไฟล์คำทักทายเป็น plain text เท่านั้น ห้ามเป็น JSON")
WORK_PRODUCT_A = ("In this product repo, create app.js containing `console.log('hi')` and commit only that file as `feat: app`. "
                  "Later steps, not now: add app.test.js, then open an MR.")
WORK_PRODUCT_B = ("Create index.html containing `<h1>hi</h1>` and commit only that file as `feat: page`. "
                  "Later steps, not now: add style.css, then deploy a preview.")
PHRASE = "let's handoff here and forward to continue work in next session"


def sh(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"{cmd}\n{r.stderr}")
    return r.stdout.rstrip()


def git_init(path, remote=None, psi=True, claude_md=None, exclude=(".claude/skills/",), fetch_url=None):
    os.makedirs(path)
    sh("git init -q -b main && git config user.name 'Test User' && git config user.email test@example.invalid", cwd=path)
    if claude_md:
        open(f"{path}/CLAUDE.md", "w").write(claude_md)
    open(f"{path}/notes.md", "w").write("# notes\n")
    if psi:
        for d in (f"{PSI}/inbox/handoff", f"{PSI}/memory/learnings"):
            os.makedirs(f"{path}/{d}")
            open(f"{path}/{d}/.gitkeep", "w").close()
    with open(f"{path}/.git/info/exclude", "a") as f:
        f.write("".join(e + "\n" for e in exclude))
    sh("git add -A && git commit -q -m init", cwd=path)
    if remote:
        sh(f"git init -q --bare -b main {remote}")
        sh(f"git remote add origin {remote} && git push -q -u origin main", cwd=path)
        if fetch_url:  # gh reads visibility from the fetch URL; pushurl keeps every push in the local bare repo
            sh(f"git remote set-url origin {fetch_url} && git remote set-url --push origin {remote}", cwd=path)


def install_skill(repo):
    if SKILL_SRC:
        d = f"{repo}/.claude/skills/handover-next"
        os.makedirs(d, exist_ok=True)
        txt = open(SKILL_SRC).read().replace("\nname: handover\n", "\nname: handover-next\n", 1)
        open(f"{d}/SKILL.md", "w").write(txt)


def claude(cwd, prompt, sid=None, resume=None, timeout=1200):
    # auto: the classifier allows routine git/file work and denies risky actions (reported in permission_denials);
    # strict-mcp-config: no MCP servers, so nested sessions get no Jira/Figma/Discord tools.
    args = [NCLAUDE, "-p", prompt, "--output-format", "json", "--permission-mode", "auto", "--strict-mcp-config"]
    args += ["--session-id", sid] if sid else []
    args += ["--resume", resume] if resume else []
    t = time.time()
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        d = json.loads(r.stdout)
    except Exception as e:  # noqa: BLE001 - report, never hide
        d = {"result": None, "error": repr(e)[:300]}
    d["_secs"] = round(time.time() - t)
    return d


def tools_after_last(sid, marker):
    """Tool calls made after the LAST user turn containing marker (works whether --resume reuses the file or forks it)."""
    tools = []
    for f in glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl")):
        for line in open(f, errors="ignore"):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("type") == "user" and marker in line and '"tool_result"' not in line:
                tools = []
            if d.get("type") != "assistant":
                continue
            for c in d.get("message", {}).get("content") or []:
                if not (isinstance(c, dict) and c.get("type") == "tool_use"):
                    continue
                n, i = c["name"], c.get("input", {})
                if n == "Skill":
                    tools.append(f"Skill({i.get('skill')}|{i.get('args', '')})")
                elif n in ("EnterPlanMode", "ExitPlanMode"):
                    tools.append(n)
                elif n == "Bash" and re.search(r"git (add|commit|push|reset|restore)", i.get("command", "")):
                    tools.append("Bash: " + re.sub(r"\s+", " ", i["command"])[:110])
                elif n in ("Write", "Edit"):
                    tools.append(f"{n}: ...{i.get('file_path', '')[-60:]}")
    return tools


def ls(path):
    return sorted(x for x in os.listdir(path) if x != ".gitkeep") if os.path.isdir(path) else []


def repo_state(repo, remote=None):
    st = {
        "head": sh("git log -1 --format='%h %s'", cwd=repo),
        "head_files": sh("git -c core.quotepath=false show --name-only --format= HEAD", cwd=repo).splitlines(),
        "head_last_line": (sh("git log -1 --format=%B", cwd=repo).strip().splitlines() or [""])[-1],
        "status": sh("git -c core.quotepath=false status --porcelain", cwd=repo).splitlines(),
        "commits": int(sh("git rev-list --count HEAD", cwd=repo)),
    }
    if remote:
        st["remote_head_equals_local"] = sh("git rev-parse HEAD", cwd=repo) == sh("git rev-parse main", cwd=remote)
    return st


def headings(path):
    return [l.strip() for l in open(path, errors="ignore") if l.startswith("#")] if os.path.isfile(path) else []


def scen_oracle(name, second_prompt, rerun=False, work=WORK_ORACLE, fetch_url=None):
    base = f"{RUN}/{name}"
    repo, remote = f"{base}/test-oracle", f"{base}/remote.git"
    os.makedirs(base)
    git_init(repo, remote=remote, claude_md=ORACLE_MD, fetch_url=fetch_url)
    install_skill(repo)
    sid = str(uuid.uuid4())
    r1 = claude(repo, work, sid=sid)
    open(f"{repo}/{PSI}/memory/other-window-note.md", "w").write("written by another window\n")
    with open(f"{repo}/notes.md", "a") as f:
        f.write("edited by another window\n")
    r2 = claude(repo, second_prompt, resume=sid)
    sid2 = r2.get("session_id") or sid
    docs = ls(f"{repo}/{PSI}/inbox/handoff")
    out = {
        "r1_ok": not r1.get("is_error"), "r2_reply": r2.get("result"), "denials": (r1.get("permission_denials") or []) + (r2.get("permission_denials") or []), "secs": [r1["_secs"], r2["_secs"]],
        "model": list((r2.get("modelUsage") or {}).keys()), "same_sid_on_resume": sid2 == sid,
        "psi_docs": docs, "claude_handovers": ls(f"{repo}/.claude/handovers"),
        "doc_headings": headings(f"{repo}/{PSI}/inbox/handoff/{docs[-1]}") if docs else [],
        "state": repo_state(repo, remote), "tools": tools_after_last(sid2, second_prompt[:40]),
    }
    if rerun:
        before = repo_state(repo, remote)
        r3 = claude(repo, second_prompt, resume=sid2)
        out["rerun"] = {"reply": r3.get("result"), "psi_docs": ls(f"{repo}/{PSI}/inbox/handoff"),
                        "head_unchanged": repo_state(repo, remote)["head"] == before["head"],
                        "tools": tools_after_last(r3.get("session_id") or sid2, second_prompt[:40])}
    return out


def scen_symlink(name):
    base = f"{RUN}/{name}"
    oracle, oremote = f"{base}/oracle-b", f"{base}/oracle-remote.git"
    prod, premote = f"{base}/product-a", f"{base}/product-remote.git"
    os.makedirs(base)
    git_init(oracle, remote=oremote, claude_md=ORACLE_MD)
    git_init(prod, remote=premote, psi=False, exclude=(".claude/skills/", PSI))
    os.symlink(f"../oracle-b/{PSI}", f"{prod}/{PSI}")
    install_skill(prod)
    sid = str(uuid.uuid4())
    r1 = claude(prod, WORK_PRODUCT_A, sid=sid)
    r2 = claude(prod, INVOKE, resume=sid)
    sid2 = r2.get("session_id") or sid
    docs = ls(f"{oracle}/{PSI}/inbox/handoff")
    return {
        "r1_ok": not r1.get("is_error"), "r2_reply": r2.get("result"), "denials": (r1.get("permission_denials") or []) + (r2.get("permission_denials") or []), "secs": [r1["_secs"], r2["_secs"]],
        "oracle_psi_docs": docs, "product_claude_handovers": ls(f"{prod}/.claude/handovers"),
        "doc_headings": headings(f"{oracle}/{PSI}/inbox/handoff/{docs[-1]}") if docs else [],
        "oracle_state": repo_state(oracle, oremote), "product_state": repo_state(prod, premote),
        "tools": tools_after_last(sid2, INVOKE),
    }


def scen_no_psi(name):
    base = f"{RUN}/{name}"
    prod, premote = f"{base}/product-b", f"{base}/product-remote.git"
    os.makedirs(base)
    git_init(prod, remote=premote, psi=False)
    install_skill(prod)
    sid = str(uuid.uuid4())
    r1 = claude(prod, WORK_PRODUCT_B, sid=sid)
    r2 = claude(prod, INVOKE, resume=sid)
    sid2 = r2.get("session_id") or sid
    hv = ls(f"{prod}/.claude/handovers")
    return {
        "r1_ok": not r1.get("is_error"), "r2_reply": r2.get("result"), "denials": (r1.get("permission_denials") or []) + (r2.get("permission_denials") or []), "secs": [r1["_secs"], r2["_secs"]],
        "claude_handovers": hv, "psi_created": os.path.exists(f"{prod}/{PSI}"),
        "doc_headings": headings(f"{prod}/.claude/handovers/{hv[-1]}") if hv else [],
        "state": repo_state(prod, premote), "tools": tools_after_last(sid2, INVOKE),
    }


JOBS = {
    "B0": lambda: scen_oracle("B0", INVOKE),
    "T1": lambda: scen_oracle("T1", INVOKE, rerun=True),
    "T1b": lambda: scen_oracle("T1b", INVOKE),
    "T6": lambda: scen_oracle("T6", INVOKE, work=WORK_ORACLE_TH),
    "T7": lambda: scen_oracle("T7", INVOKE, fetch_url="https://github.com/switchaphon/leica-oracle"),     # PUBLIC
    "T8": lambda: scen_oracle("T8", INVOKE, fetch_url="https://github.com/switchaphon/pops-vet-oracle"),  # PRIVATE
    "T2": lambda: scen_symlink("T2"),
    "T3": lambda: scen_no_psi("T3"),
    "T5": lambda: scen_oracle("T5", PHRASE),
}

if __name__ == "__main__":
    os.makedirs(RUN, exist_ok=False)
    results = {}
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(JOBS[s]): s for s in SCENS}
        for fu in cf.as_completed(futs):
            s = futs[fu]
            try:
                results[s] = fu.result()
            except Exception as e:  # noqa: BLE001
                results[s] = {"crash": repr(e)[:500]}
    json.dump(results, open(f"{RUN}/results.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(results, ensure_ascii=False, indent=1))
