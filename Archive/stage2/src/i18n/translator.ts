import type { SupportedLanguage } from "@i18n/strings";

export interface ContentTranslator {
  translateNodeLabel: (text: string, metadata?: Record<string, unknown>) => string;
  translateEdgeLabel: (text: string | undefined, metadata?: Record<string, unknown>) => string | undefined;
}

export function createContentTranslator(language: SupportedLanguage): ContentTranslator {
  if (language === "zh") {
    return {
      translateNodeLabel: (text, metadata) => translateWithFallback(text, metadata, "zh"),
      translateEdgeLabel: (text, metadata) =>
        text ? translateWithFallback(text, metadata, "zh") : text
    };
  }

  return {
    translateNodeLabel: (text) => text,
    translateEdgeLabel: (text) => text
  };
}

function translateWithFallback(
  text: string,
  metadata: Record<string, unknown> | undefined,
  language: SupportedLanguage
): string {
  if (!text) {
    return text;
  }

  const metaTranslation = getMetadataTranslation(metadata, language);
  if (metaTranslation) {
    return metaTranslation;
  }

  if (language === "zh") {
    return englishToChineseFallback(text);
  }

  return text;
}

function getMetadataTranslation(
  metadata: Record<string, unknown> | undefined,
  language: SupportedLanguage
): string | undefined {
  if (!metadata) return undefined;
  const translations = metadata.translations as Record<string, string> | undefined;
  if (!translations) return undefined;
  return translations[language];
}

function englishToChineseFallback(text: string): string {
  const dictionary: Record<string, string> = {
    "System Boot": "系统启动",
    "Firmware starts and prepares to initialize hardware and state.": "固件启动并准备初始化硬件与状态。",
    "Initialize peripherals, globals, queues": "初始化外设、全局变量和队列",
    "Set up UART/OLED, key event queue, flash mappings, and menu state flags.": "设置 UART/OLED、按键事件队列、Flash 映射以及菜单状态标志。",
    "Flash_Task main loop": "Flash_Task 主循环",
    "Forever loop reacts to system states, timers, and key events.": "在循环中响应系统状态、定时器和按键事件。",
    "SYSTEM_IDLE handling": "处理 SYSTEM_IDLE 状态",
    "Manages idle timers, disconnects BLE, enters low power, waits for activity.": "管理空闲计时器、断开 BLE、进入低功耗并等待活动。",
    "MENU_ACTIVE → run main menu": "MENU_ACTIVE → 运行主菜单",
    "Shows icon menu, reads user choice, and dispatches to handlers.": "显示图标菜单，读取用户选择并分派到对应处理流程。",
    "Main icon selection": "主图标选择",
    "User picks Configure, Else Mode, Delete, or Back via key presses.": "用户通过按键选择配置、其他模式、删除或返回。",
    "handle_config_menu": "执行配置菜单",
    "Loads user settings, runs angle/speed menu, saves config to flash on confirm.": "加载用户设置，进入角度/速度菜单，并在确认后保存到 Flash。",
    "menu3_angle_speed loop": "角度/速度配置循环",
    "Cycle through Angle, Speed, Auto-close, Save, Exit options, updating OLED each change.": "循环浏览角度、速度、自动关闭、保存、退出选项并实时更新 OLED。",
    "handle_delete_menu": "执行删除菜单",
    "Runs delete menu, triggers reset-all or single-user deletion with progress feedback.": "运行删除菜单，触发全部重置或单个删除并显示进度。",
    "handle_else_mode_menu": "执行其他模式菜单",
    "Manages Do Not Disturb toggle, door calibration shortcut, or return.": "管理勿扰模式切换、门校准快捷方式或返回。",
    "handle_Reset_menu door calibration": "门校准流程",
    "Guides user through opening door, shows 10s progress bar, confirms success.": "引导用户打开门，显示 10 秒进度条并确认成功。",
    "Do Not Disturb state": "勿扰模式",
    "Silences UI, shows minimal screen, exits on key press or timeout.": "静音界面，显示极简屏幕，按键或超时退出。",
    "Face enrollment/delete states": "人脸录入/删除状态",
    "Displays success/failure messages for face recognition operations and returns to menu.": "显示人脸识别操作的成功/失败信息并返回菜单。",
    "Flash read/write helpers": "Flash 读写工具",
    "Utility routines for aligned writes, CRC checks, BLE address persistence.": "提供对齐写入、CRC 校验以及 BLE 地址保存等工具函数。",
    "System continues running": "系统持续运行",
    "Loop persists indefinitely, awaiting further user input or events.": "循环持续运行，等待更多用户输入或事件。",
    "state == SYSTEM_IDLE": "状态 == SYSTEM_IDLE",
    "state == MENU_ACTIVE": "状态 == MENU_ACTIVE",
    "DND flag set": "启用勿扰标志",
    "state == FACE_*": "进入人脸处理状态",
    "Load/save config or BLE address": "加载/保存配置或 BLE 地址",
    "Timer / event wakes system": "定时器/事件唤醒系统",
    "Key2 selects Configure": "按键 2 选择配置",
    "Key2 selects Else Mode": "按键 2 选择其他模式",
    "Key2 selects Delete": "按键 2 选择删除",
    "Back to idle": "返回空闲",
    "Enter angle/speed menu": "进入角度/速度菜单",
    "Save or exit": "保存或退出",
    "Persist configuration": "持久化配置",
    "Return to menu": "返回菜单",
    "Erase flash records": "擦除 Flash 记录",
    "Deletion finished": "删除完成",
    "Toggle DND": "切换勿扰模式",
    "Door reset option": "门复位选项",
    "Back": "返回",
    "Calibration done": "校准完成",
    "Exit DND": "退出勿扰模式",
    "Show result → idle/menu": "显示结果 → 空闲/菜单",
    "Loop continues": "循环继续"
  };

  const exact = dictionary[text];
  if (exact) {
    return exact;
  }

  const lowered = text.toLowerCase();
  for (const [key, value] of Object.entries(dictionary)) {
    if (lowered.includes(key.toLowerCase())) {
      return value;
    }
  }

  return text;
}
