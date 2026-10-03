#ifndef LIC_DSF_LAUNCHER_PLAN_H
#define LIC_DSF_LAUNCHER_PLAN_H
#include <stdint.h>
#include <wchar.h>
#define LAUNCHER_CAP 32768
/* Windows WCHAR capacity, including the terminating NUL. */
typedef struct {
    wchar_t root[LAUNCHER_CAP];
    wchar_t python[LAUNCHER_CAP];
    wchar_t script[LAUNCHER_CAP];
    wchar_t command[LAUNCHER_CAP];
} LauncherPlan;
int launcher_plan(const wchar_t *module_path, int verify_only, LauncherPlan *plan);
int launcher_verify_mode(int argc, const wchar_t *const *argv);
/* 0 = quiet success/cancellation, 1 = pause/error, 2 = pause/check success. */
int launcher_exit_action(uint32_t child_status, int verify_only);
#endif
