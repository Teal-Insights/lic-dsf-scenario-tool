/* Unsigned Windows source preparation. Native compilation/acceptance pending. */
#ifndef _WIN32
#error This translation unit requires Windows SDK headers and an x64 MSVC environment.
#endif
#if defined(_MSC_VER) && _MSC_VER < 1928
#error C17 preparation requires MSVC 2019 version 16.8 or later.
#endif
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "launcher_plan.h"

static BOOL WINAPI parent_control(DWORD event) {
    /* A real custom parent handler, not the inheritable NULL/TRUE ignore flag.
       The bundled Python child receives its own console control notifications. */
    return event == CTRL_C_EVENT || event == CTRL_BREAK_EVENT;
}

static void pause_for_enter(void) {
    wint_t ch;
    fputws(L"\nPress Enter to close this launcher.\n", stdout);
    fflush(stdout);
    do { ch = fgetwc(stdin); } while (ch != L'\n' && ch != WEOF);
}

static int failed(const wchar_t *message) {
    fputws(message, stderr);
    fputws(L"\nPlease record the message. Do not disable Windows protections.\n", stderr);
    pause_for_enter();
    return 1;
}

static int missing_runtime(void) {
    fputws(L"\nThe program files are missing from this folder.\n\n"
            L"Start LIC-DSF.exe could not find runtime\\python.exe beside it.\n"
            L"Two things usually cause this:\n"
            L"  - The launcher was opened from inside the ZIP.\n"
            L"  - The ZIP was only partly extracted, or files were moved or deleted.\n\n"
            L"Extracting a fresh, complete copy fixes both:\n"
            L"  1. Close this window.\n"
            L"  2. Find the ZIP file you downloaded, usually in Downloads.\n"
            L"  3. Right-click the ZIP file and choose Extract All.\n"
            L"  4. Choose Extract and wait for Windows to finish.\n"
            L"  5. Open the folder Windows created.\n"
            L"  6. Double-click Start LIC-DSF.exe inside that folder.\n\n"
            L"Keep every extracted file together in one folder.\n", stdout);
    pause_for_enter();
    return 1;
}

int wmain(int argc, wchar_t **argv) {
    wchar_t module[LAUNCHER_CAP];
    LauncherPlan *plan;
    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION process = {0};
    DWORD length, attributes, status = 0, waited;
    BOOL got_status, thread_closed, process_closed, handler_removed;
    int verify_only = launcher_verify_mode(argc, (const wchar_t *const *)argv);
    int action;
    if (verify_only < 0) return failed(L"Use Start LIC-DSF.exe with no arguments, or with --verify-only. Other arguments are not supported.");
    length = GetModuleFileNameW(NULL, module, LAUNCHER_CAP);
    if (length == 0 || length >= LAUNCHER_CAP) return failed(L"The launcher could not determine its package folder.");
    plan = calloc(1, sizeof(*plan));
    if (plan == NULL) return failed(L"The launcher could not allocate its path buffers.");
    if (!launcher_plan(module, verify_only, plan)) {
        free(plan);
        return failed(L"The package path cannot be used, or is too long for this launcher.");
    }
    attributes = GetFileAttributesW(plan->python);
    if (attributes == INVALID_FILE_ATTRIBUTES || (attributes & FILE_ATTRIBUTE_DIRECTORY) != 0) {
        free(plan);
        return missing_runtime();
    }
    if (!SetConsoleCtrlHandler(parent_control, TRUE)) {
        free(plan);
        return failed(L"The launcher could not prepare console control handling.");
    }
    startup.cb = sizeof(startup);
    /* Exact bundled interpreter, mutable command line and explicit package cwd.
       Inherit the environment/std console; do not inherit arbitrary handles. */
    if (!CreateProcessW(plan->python, plan->command, NULL, NULL, FALSE, 0,
                        NULL, plan->root, &startup, &process)) {
        SetConsoleCtrlHandler(parent_control, FALSE);
        free(plan);
        return failed(L"The local workspace could not start. Verify the complete package or use the preserved CMD fallback.");
    }
    waited = WaitForSingleObject(process.hProcess, INFINITE);
    got_status = waited == WAIT_OBJECT_0 && GetExitCodeProcess(process.hProcess, &status);
    thread_closed = CloseHandle(process.hThread);
    process_closed = CloseHandle(process.hProcess);
    handler_removed = SetConsoleCtrlHandler(parent_control, FALSE);
    free(plan);
    if (!got_status) return failed(L"The launcher could not confirm the tool's exit status. It does not claim the tool has stopped.");
    if (!thread_closed || !process_closed || !handler_removed) return failed(L"The tool ended, but the launcher could not confirm normal cleanup.");
    action = launcher_exit_action(status, verify_only);
    if (action == 1) {
        fwprintf(stderr, L"The tool stopped unexpectedly with status %ld.\n", (long)(int32_t)status);
        return failed(L"The operation did not finish normally.");
    }
    if (action == 2) pause_for_enter();
    return 0;
}
