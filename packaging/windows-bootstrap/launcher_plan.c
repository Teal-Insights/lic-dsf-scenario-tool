#include "launcher_plan.h"
#include <stddef.h>
#include <string.h>

static int append(wchar_t *out, const wchar_t *text) {
    size_t used = wcslen(out), extra = wcslen(text);
    if (extra >= LAUNCHER_CAP || used >= LAUNCHER_CAP - extra) return 0;
    wmemcpy(out + used, text, extra + 1);
    return 1;
}

int launcher_plan(const wchar_t *module_path, int verify_only, LauncherPlan *plan) {
    size_t length, cut = 0, i;
    if (module_path == NULL || plan == NULL || (verify_only != 0 && verify_only != 1)) return 0;
    memset(plan, 0, sizeof(*plan));
    length = wcslen(module_path);
    if (length == 0 || length >= LAUNCHER_CAP) return 0;
    if (!((length >= 3 && module_path[1] == L':' && module_path[2] == L'\\') ||
          (length >= 3 && module_path[0] == L'\\' && module_path[1] == L'\\'))) return 0;
    for (i = 0; i < length; ++i) {
        if (module_path[i] == L'"' || module_path[i] < 32) return 0;
        if (module_path[i] == L'\\') cut = i + 1;
    }
    if (cut == 0 || cut == length) return 0;
    /* Keep the root's separator, including drive and UNC/extended prefixes. */
    wmemcpy(plan->root, module_path, cut);
    if (!append(plan->python, plan->root) || !append(plan->python, L"runtime\\python.exe") ||
        !append(plan->script, plan->root) || !append(plan->script, L"start_local.py")) return 0;
    /* Both paths end in fixed filenames, never a trailing backslash or quote.
       No cmd.exe interpretation or environment/PATH executable lookup occurs. */
    if (!append(plan->command, L"\"") || !append(plan->command, plan->python) ||
        !append(plan->command, L"\" -X utf8 -B \"") || !append(plan->command, plan->script) ||
        !append(plan->command, L"\"")) return 0;
    if (verify_only && !append(plan->command, L" --verify-only")) return 0;
    return 1;
}

int launcher_verify_mode(int argc, const wchar_t *const *argv) {
    if (argc == 1) return 0;
    if (argc == 2 && argv != NULL && argv[1] != NULL && wcscmp(argv[1], L"--verify-only") == 0) return 1;
    return -1;
}

int launcher_exit_action(uint32_t child_status, int verify_only) {
    if (child_status == UINT32_C(0xc000013a)) return 0;
    if (child_status != 0) return 1;
    return verify_only ? 2 : 0;
}
