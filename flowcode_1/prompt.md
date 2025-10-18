# Flowchart Prompt Template

Copy your source code or project description below. The generator script will send this entire file to the LLM, so keep it concise and focused on the logic you want explained.

---

```
// Paste code or narrative here
#include "main.h"
#include "cmsis_os.h"
#include "FreeRTOS.h"
#include "task.h"
#include "Flash.h"
#include "stm32_flash_operations.h"
#include "face_recognition.h"
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include "usart.h"
#include "gpio.h"
#include "stm32l4xx_hal_gpio.h"
#include "OLED_driver.h"
#include "OLED.h"  // 包含图形绘制函数和宏定义
#include "bluetooth_comm.h"  // 包含HC15_SendMessage函数声明
#include "ld2450_integration.h"  // 包含LD2450雷达集成模块
#include "power_management.h"
#include "xy_mb06ba.h"
#include "battery_sensor.h"  // 包含电池传感器接口
extern bool Connected_Success;





// === Added: DIY frame sender over UART1 (binary 6B: FA CE | UIDL UIDH | (S<<4|A) | CRC8) ===
extern UART_HandleTypeDef huart2;



static uint8_t crc8_maxim_calc_flash(const uint8_t *data, uint8_t len)
{
    uint8_t crc = 0x00;
    for (uint8_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            crc = (crc & 0x01) ? (crc >> 1) ^ 0x8C : (crc >> 1);
        }
    }
    return crc;
}

__attribute__((unused)) static void FLASH_SendDIYFrame_UART1(uint16_t uid, uint8_t angle_idx, uint8_t speed_idx, uint8_t open_flag)
{
    uint8_t frm[7];  // 增加一个字节来存储open_flag
    frm[0] = 0xFA;
    frm[1] = 0xCE;
    frm[2] = (uint8_t)(uid & 0xFF);
    frm[3] = (uint8_t)((uid >> 8) & 0xFF);
    frm[4] = (uint8_t)((speed_idx & 0x0F) << 4) | (uint8_t)(angle_idx & 0x0F);
    frm[5] = open_flag & 0xFF;  // 开关标志位
    frm[6] = crc8_maxim_calc_flash(frm, 6);
    HAL_UART_Transmit_IT(&huart2, frm, sizeof(frm));
}
// === End added ===

/* ===== Flash地址布局说明 =====
 * STM32L431 Flash总容量: 256KB (0x08000000 ~ 0x08040000)
 * 
 * Flash分区布局:
 * ┌──────────────────────────────────────────────────────┐
 * │ 程序代码区域: 0x08000000 ~ 0x0803C000 (240KB)        │
 * ├──────────────────────────────────────────────────────┤
 * │ 用户数据区域: 0x0803C000 ~ 0x0803F800 (14KB, 56用户) │
 * ├──────────────────────────────────────────────────────┤
 * │ 蓝牙地址区域: 0x0803F800 ~ 0x08040000 (2KB, 独立)   │
 * └──────────────────────────────────────────────────────┘
 * 
 * 这种布局完全避免了地址冲突，确保各功能模块独立运行
 */
#define FLASH_USER_BASE_ADDR     0x0803C000  // 用户数据区域起始地址
#define FLASH_USER_END_ADDR      0x0803F800  // 用户数据区域结束地址(预留蓝牙地址空间)
#define USER_CONFIG_FLASH_SIZE   0x100       // 每个用户使用 256 字节
#define MAX_USER_CONFIG_COUNT    56          // 最多支持 56 个用户（14KB / 256B，避免与蓝牙地址冲突）
 
user_config_t temp_cfg;

// 在文件开头添加菜单验证标志
bool flash_write_flag = false;
bool Delete = false;
bool match_enroll_flag = false;
bool enroll_success = false;
bool face_enroll_in_progress = false;

// 勿扰模式标志位
bool silent_do_not_disturb = false;  // 静默勿扰模式标志位

bool pre_Sleep_Flag = false;

// 注册进度条动画状态变量
bool enroll_progress_active = false;
uint32_t enroll_progress_start_time = 0;
uint32_t enroll_progress_duration = 3000;  // 3秒固定时长


int save_choice = 1;
extern bool all_control;
volatile SystemState_t system_state = SYSTEM_IDLE;
volatile uint32_t debug_flash_address = 0x0803C000;

extern uint16_t userid;
extern bool delete_success;
extern uint16_t g_FaceRecUserID;
extern bool face_rec_running;
user_config_t user_cfg_diy;
uint8_t key_num = 0;
uint8_t delete_num = 0;
uint8_t flag_change = 1;
uint8_t flag = 1;
uint8_t Menu = 1;
uint8_t speed_mode = 0;
uint8_t angle_mode = 0;
uint8_t selected_user_id = 0;  // 新增：选中的用户ID

// 新增：全局调试变量
uint8_t debug_change_state = 0;  // 0=选择用户ID, 1=选择角度速度, 2=确认存储
uint8_t debug_temp_angle = 0;    // 临时角度设置
uint8_t debug_temp_speed = 0;    // 临时速度设置
uint8_t debug_open_or_not_flag = 0;    // 临时开或关设置
bool debug_config_changed = false; // 配置是否被修改
// 菜单状态枚举
typedef enum {
    MENU_LEVEL_1 = 1,
    MENU_LEVEL_2_DELETE,
    MENU_LEVEL_2_CHANGE,
    MENU_LEVEL_2_CHECK,
    MENU_LEVEL_3_DELETE_ALL,
    MENU_LEVEL_3_DELETE_SINGLE,
    MENU_LEVEL_3_CHANGE_SPEED,
    MENU_LEVEL_3_CHANGE_ANGLE,
    MENU_LEVEL_4_SPEED_FAST,
    MENU_LEVEL_4_SPEED_MEDIUM,
    MENU_LEVEL_4_SPEED_SLOW,
    MENU_LEVEL_4_ANGLE_90,
    MENU_LEVEL_4_ANGLE_120,
    MENU_LEVEL_4_ANGLE_180
} MenuLevel_t;

// 函数声明
void handle_config_menu(void);
void handle_verify_menu(void);
void handle_delete_menu(void);
void handle_change_menu(void);
void handle_check_menu(void);
void process_main_menu(int menu_choice);

// Flash相关函数声明
static uint8_t calculate_crc(const user_config_t *cfg);
static Flash_Status Flash_Write64BitAligned(uint32_t address, const void* data, uint32_t size);

int menu3_angle_speed(void);

// ========= 按键事件队列与兼容接口（支持独立扫描线程） =========
// 说明：
// - 外部高频线程可循环调用 Get_key_Num()，将非零事件通过 KeyEvent_Push() 放入队列；
// - 菜单/界面逻辑统一使用 Key_GetEvent() 获取事件：
//     1) 若队列有数据，则直接弹出；
//     2) 若队列为空且未启用外部扫描模式，则回退调用 Get_key_Num()，保持旧行为兼容；
//     3) 若队列为空且已启用外部扫描模式，则返回 0。

static volatile int s_key_evt_queue[16];
static volatile uint8_t s_key_evt_head = 0; // 写入位置
static volatile uint8_t s_key_evt_tail = 0; // 读取位置
static volatile uint8_t s_key_evt_count = 0; // 当前元素个数
static volatile bool s_key_scan_external = false; // true 表示已启用外部扫描线程

void Key_Scan_SetExternalMode(bool enable)
{
	s_key_scan_external = enable;
}

static inline bool keyevt_pop(int *out)
{
	if (s_key_evt_count == 0) return false;
	taskENTER_CRITICAL();
	if (s_key_evt_count == 0) {
		taskEXIT_CRITICAL();
		return false;
	}
	int val = s_key_evt_queue[s_key_evt_tail];
	s_key_evt_tail = (uint8_t)((s_key_evt_tail + 1U) & 0x0F);
	s_key_evt_count--;
	taskEXIT_CRITICAL();
	if (out) *out = val;
	return true;
}

void KeyEvent_Push(int code)
{
	if (code == 0) return;
	taskENTER_CRITICAL();
	if (s_key_evt_count < (uint8_t)(sizeof(s_key_evt_queue)/sizeof(s_key_evt_queue[0]))) {
		s_key_evt_queue[s_key_evt_head] = code;
		s_key_evt_head = (uint8_t)((s_key_evt_head + 1U) & 0x0F);
		s_key_evt_count++;
	} else {
		// 队列满：丢弃最旧，插入新事件（保证最新事件不丢）
		s_key_evt_tail = (uint8_t)((s_key_evt_tail + 1U) & 0x0F);
		s_key_evt_queue[s_key_evt_head] = code;
		s_key_evt_head = (uint8_t)((s_key_evt_head + 1U) & 0x0F);
		// s_key_evt_count 不变（保持满）
	}
	taskEXIT_CRITICAL();
}

// 菜单消费接口：优先消费队列事件；否则根据外部扫描模式决定是否回退调用 Get_key_Num()
int Key_GetEvent(void)
{
	int ev = 0;
	if (keyevt_pop(&ev)) return ev;
	if (!s_key_scan_external) {
		// 兼容：无外部扫描线程时，直接调用旧接口
		return Get_key_Num();
	}
	return 0;
}

// 可选：提供一个扫描任务模板，方便放到独立线程中使用
// 用法：在线程入口运行此函数或复制代码：
// void Key_ScanTask(void *argument) {
//     Key_Scan_SetExternalMode(true);
//     for(;;) {
//         int e = Get_key_Num();
//         if (e) KeyEvent_Push(e);
//         osDelay(1); // 高频扫描
//     }
// }

// 阻塞式居中进度条（使用 HAL_GetTick 计时；循环内 osDelay 让出 CPU）
static void Flash_ShowBlockingProgress(uint32_t duration_ms)
{
	// 进度条参数
	const int16_t bar_width = 108;   // 与 OLED 示例一致
	const int16_t bar_height = PROGRESS_BAR_HEIGHT; // 来自 OLED.h 宏
	const int16_t x = (int16_t)((OLED_WIDTH - bar_width) / 2);
	const int16_t y = (int16_t)((OLED_HEIGHT - bar_height) / 2);

	// 初始化画面
	OLED_Clear();
	OLED_ShowStringCentered(y - 14, "Calibrating...", OLED_6X8_HALF);
	OLED_Update();

	uint32_t start = HAL_GetTick();
	uint32_t now = start;
	uint32_t last_draw = 0;

	while ((now - start) < duration_ms) {
		now = HAL_GetTick();
		uint32_t elapsed = now - start;
		if (elapsed > duration_ms) elapsed = duration_ms;
		// 0~100 线性映射
		uint8_t progress = (uint8_t)((elapsed * 100U) / (duration_ms ? duration_ms : 1U));

		// 节流重绘：每 20ms 重绘一次，避免刷新过快
		if ((now - last_draw) >= 20U || progress >= 100U) {
			// 清理进度区域并重画
			OLED_ClearArea(x - 2, y - 2, bar_width + 4, bar_height + 4);
			OLED_ShowProgressBar(x, y, bar_width, progress, PROGRESS_SPEED_FAST);
			OLED_Update();
			last_draw = now;
		}

		osDelay(5); // 释放 CPU，避免硬阻塞
	}
}


// 按键状态结构体
typedef struct {
    uint8_t last_state;        // 上次按键状态
    uint8_t current_state;     // 当前按键状态
    uint8_t debounced_state;   // 防抖后的稳定状态
    uint32_t last_change_time; // 上次状态改变时间
    uint8_t pressed_flag;      // 按键按下标志（确保只触发一次）
    uint32_t press_start_time; // 按键开始按下的时间
    uint8_t long_press_flag;   // 长按标志（确保只触发一次）
} key_state_t;

// ================== 按键扫描/防抖参数配置 ==================
// 扫描周期：调用 Get_key_Num 的最小间隔（函数内部做节流）。
// 如果外层任务循环很快，无需修改；若想统一管理，可把 5 改为宏。
// 典型机械按键抖动 2~10ms，推荐：
//   KEY_DEBOUNCE_TIME_MS 15~30ms 之间可消除大部分抖动
//   KEY_LONG_PRESS_TIME_MS 1200~1500ms 更贴近日常“长按”感受
// 注意：短按是否被识别，与“按下稳定 + 释放稳定”总时间是否 >= 去抖时间 成正相关。
// 本实现保证：即使按下时间极短（< 去抖时间）但总按压+释放仍跨越两个稳定判定，也会报告一次短按。
// ==========================================================
#define KEY_SCAN_INTERVAL_MS    0      // 扫描调用最小间隔（节流用）
#define KEY_DEBOUNCE_TIME_MS    0     // 防抖确认阈值（ms）
#define KEY_LONG_PRESS_TIME_MS  1500   // 长按判定时间（ms）

// 静态按键状态变量
static key_state_t key_states[3] = {0};

// 新的内部状态机：
// IDLE(稳定释放) -> BOUNCE_PRESS(检测到可能按下) -> PRESSED(稳定按下) -> LONG_REPORTED(已上报长按，可继续保持) -> BOUNCE_RELEASE(检测到可能释放) -> IDLE
// 由于资源受限，不单独再建枚举，使用结构中的字段组合实现。

typedef enum {
	BTN_STAGE_IDLE = 0,
	BTN_STAGE_BOUNCE_PRESS,
	BTN_STAGE_PRESSED,
	BTN_STAGE_LONG_REPORTED,
	BTN_STAGE_BOUNCE_RELEASE
} btn_stage_t;

typedef struct {
	btn_stage_t stage;          // 当前阶段
	uint8_t stable_level;       // 当前稳定逻辑电平(0=未按 1=按下)
	uint32_t stage_start_tick;  // 阶段开始时间
	uint32_t press_tick;        // 确认按下的时间（用于长按计时）
	uint8_t long_sent;          // 长按是否已发送
} btn_fsm_t;

static btn_fsm_t btn_fsm[3] = {0};

// 改进的按键防抖函数 - 非阻塞式，支持长按检测
// 返回值：1-3表示短按按键1-3，11-13表示长按按键1-3，0表示无按键
int Get_key_Num(void)
{

    Battery_Update();
    info = Battery_GetInfo();
	OLED_Battery_SetLevel(info.percentage);

	HC15_SendMessage("AA0055");
	static uint32_t last_scan_tick = 0;
	uint32_t now = HAL_GetTick();

	if ((now - last_scan_tick) < KEY_SCAN_INTERVAL_MS) {
		return 0; // 节流：减少 GPIO 读与逻辑判断开销
	}
	last_scan_tick = now;

	// 读取当前原始按键电平（按下=1）
	uint8_t raw[3] = {
		(HAL_GPIO_ReadPin(PIN1_GPIO_Port, PIN1_Pin) == GPIO_PIN_RESET) ? 1 : 0,
		(HAL_GPIO_ReadPin(PIN2_GPIO_Port, PIN2_Pin) == GPIO_PIN_RESET) ? 1 : 0,
		(HAL_GPIO_ReadPin(PIN3_GPIO_Port, PIN3_Pin) == GPIO_PIN_RESET) ? 1 : 0
	};

	// 遍历每个键运行状态机
	for (int i = 0; i < 3; ++i) {
		btn_fsm_t *f = &btn_fsm[i];
		switch (f->stage) {
			case BTN_STAGE_IDLE:
				f->stable_level = 0;
				f->long_sent = 0;
				if (raw[i]) { // 可能按下
					f->stage = BTN_STAGE_BOUNCE_PRESS;
					f->stage_start_tick = now;
				}
				break;

			case BTN_STAGE_BOUNCE_PRESS:
				if (!raw[i]) { // 抖回去
					f->stage = BTN_STAGE_IDLE;
					break;
				}
				if ((now - f->stage_start_tick) >= KEY_DEBOUNCE_TIME_MS) {
					// 确认稳定按下
					f->stable_level = 1;
					f->press_tick = now;
					f->stage = BTN_STAGE_PRESSED;
				}
				break;

			case BTN_STAGE_PRESSED:
				if (!raw[i]) { // 进入释放抖动阶段
					f->stage = BTN_STAGE_BOUNCE_RELEASE;
					f->stage_start_tick = now;
				} else if (!f->long_sent && (now - f->press_tick) >= KEY_LONG_PRESS_TIME_MS) {
					f->long_sent = 1;
					f->stage = BTN_STAGE_LONG_REPORTED; // 长按阶段
					return i + 11; // 长按事件一次性返回 11/12/13
				}
				break;

			case BTN_STAGE_LONG_REPORTED:
				if (!raw[i]) { // 开始释放抖动
					f->stage = BTN_STAGE_BOUNCE_RELEASE;
					f->stage_start_tick = now;
				}
				// 保持长按后不重复返回
				break;

			case BTN_STAGE_BOUNCE_RELEASE:
				if (raw[i]) { // 抖动又回到按下
					// 根据是否曾经长按过返回相应阶段
					f->stage = f->long_sent ? BTN_STAGE_LONG_REPORTED : BTN_STAGE_PRESSED;
					break;
				}
				if ((now - f->stage_start_tick) >= KEY_DEBOUNCE_TIME_MS) {
					// 确认稳定释放
					int ret = 0;
					if (!f->long_sent) {
						// 未上报过长按 => 短按
						ret = i + 1; // 1/2/3
					}
					// 复位状态机
					f->stage = BTN_STAGE_IDLE;
					f->stable_level = 0;
					f->long_sent = 0;
					if (ret) return ret;
				}
				break;
		}
	}

	return 0; // 无事件
}

/* ================= 使用与调试说明 =================
1. 参数调优建议：
	- 如果仍偶发短按丢失，可将 KEY_DEBOUNCE_TIME_MS 从 15 降到 12，但不要低于 8，否则抗抖能力下降。
	- 如果感觉长按触发慢，可把 KEY_LONG_PRESS_TIME_MS 设为 1200。
2. 事件触发逻辑：
	- 短按：按下稳定 -> 未达到长按时间前释放稳定 -> 返回 (1/2/3)
	- 长按：按下稳定后累计时间 >= KEY_LONG_PRESS_TIME_MS 即刻返回 (11/12/13)，释放不再返回短按。
	- 极短脉冲：若按下脉冲不足以进入稳定按下阶段（< 去抖时间）不会产生事件。
3. 快速连击：两次短按之间必须在释放后再次进入稳定按下阶段，最短节拍 ≈ KEY_DEBOUNCE_TIME_MS * 2 + 人手动作时间。
4. 若需“长按重复加速”功能，可在 LONG_REPORTED 阶段加间隔定时返回重复码。
=================================================== */

// 一级菜单 - 图标式主菜单界面
int menu1(void)
{
	static uint8_t last_flag = 0;  // 记录上次的选择，避免重复刷新
	static bool first_draw = true; // 强制首次绘制
	
	// 重置flag为初始值，确保每次进入菜单都从第一项开始
	flag = 1;
	
	// 初始化图标菜单光标闪烁
	OLED_InitIconMenuCursor();
	
	// 强制刷新显示，确保每次进入菜单都会显示
	last_flag = 0;  // 重置last_flag，强制触发显示刷新
	first_draw = true;
	
	while(1)
	{

		if(system_state == Do_not_disturb)
		{
			OLED_Clear();
			OLED_Update();
			return 0;
		}

	key_num = Key_GetEvent();
		// 按键1：向左选择 (图标从左到右排列)
		if(key_num == 1 )
		{
			flag--;
			if(flag == 0 )
			{
				flag = 3;
			}
		}
		// 按键2：确认选择
		else if(key_num == 2 )
		{
			OLED_Clear();
			OLED_Update();
			return flag;
		}
		// 按键3：向右选择
		else if(key_num == 3 )
		{
			flag++;
			if(flag > 3 )
			{
				 flag = 1;
			}
		}
		// 长按按键3：进入静默勿扰模式
		else if(key_num == 13)
		{
			silent_do_not_disturb = true;  // 设置静默勿扰模式标志
			system_state = Do_not_disturb;  // 设置系统状态为勿扰模式
			OLED_Clear();
			OLED_Update();
			return 0;  // 退出菜单
		}
		else if(key_num == 12)
		{
			handle_Reset_menu();
		}

		// 绘制图标菜单界面
		bool force_redraw = (flag != last_flag) || first_draw;
		
	// 总是调用绘制函数，让它内部判断是否需要重绘
	OLED_DrawIconMenu(flag - 1, force_redraw);  // flag-1 因为索引从0开始
	// 叠加右上角电量与低电提示
	OLED_DrawBatteryIconTopRight();
	OLED_BatteryLowNotifier_Update();

	// 总是更新显示以确保闪烁效果
		OLED_Update();
		
		last_flag = flag;
		first_draw = false;
		
		osDelay(5);  // 增加延时，减少刷新频率
	}
}

// 二级菜单 - 删除选项
int menu2_delete(void)
{
	flag_change = 1;
	OLED_Clear();
	OLED_Display();
	
	while(1)
	{
	key_num = Key_GetEvent();
		// 按键1：向上选择
		if(key_num == 1 )
		{
			flag_change--;
			if(flag_change == 0 )
			{
				 flag_change = 2;
			}
			OLED_Clear();
			OLED_Display();
		}
		// 按键2：确认选择
		else if(key_num == 2 )
		{
			OLED_Clear();
			OLED_Display();
			return flag_change;
		}
		// 按键3：向下选择
		else if(key_num == 3 )
		{
			flag_change++;
			if(flag_change > 2 )
			{
				 flag_change = 1;
			}
			OLED_Clear();
			OLED_Display();
		}
		
		// 显示删除选项
		switch( flag_change )
		{
			case 1: // 重置所有
			{
				OLED_ShowStringCentered(0, "reset all", OLED_6X8_HALF);
				OLED_ShowStringCentered(16, "reset single", OLED_6X8_HALF);
				OLED_ShowStringCentered(0, "<-", OLED_6X8_HALF);
				break;
			}
			case 2: // 重置单个
			{
				OLED_ShowStringCentered(0, "reset all", OLED_6X8_HALF);
				OLED_ShowStringCentered(16, "reset single", OLED_6X8_HALF);
				OLED_ShowStringCentered(16, "<-", OLED_6X8_HALF);
				break;
			}
		}
		osDelay(5);
	}
}

// 带返回功能的菜单函数 - 返回0表示返回上一级
int menu2_delete_with_return(void)
{
	static uint8_t last_flag_change = 0;  // 记录上次的选择，避免重复刷新
	
	flag_change = 1;
	last_flag_change = 0;  // 强制重置，确保初始显示
	
	// 立即显示初始菜单
	// 显示菜单项（增强版本，保持原有逻辑）
	OLED_Clear();
	
	OLED_ShowStringCentered(16, "Reset All", OLED_6X8_HALF);
	OLED_ShowStringCentered(28, "Reset Single", OLED_6X8_HALF);
	OLED_ShowStringCentered(40, "Back", OLED_6X8_HALF);
			
	// 高亮当前选中的行
	OLED_HighlightMenuLine(flag_change - 1, true);
	// 叠加右上角电量与低电提示
	OLED_DrawBatteryIconTopRight();
	OLED_BatteryLowNotifier_Update();

	OLED_Display();
	last_flag_change = 1;  // 标记已显示
	
	while(1)
	{
	key_num = Key_GetEvent();
		if(key_num == 1 )
		{
			flag_change--;
			if(flag_change == 0 )
			{
				 flag_change = 3; // 增加返回选项
			}
		}
		else if(key_num == 2 )
		{
			OLED_Clear();
			OLED_Display();
			if(flag_change == 3) {
				return 0; // 返回上一级
			}
			return flag_change;
		}
		else if(key_num == 3 )
		{
			flag_change++;
			if(flag_change > 3 )
			{
				 flag_change = 1;
			}
		}
		
		// 只有当选择发生变化时才刷新显示
		if (flag_change != last_flag_change) {
			// 显示菜单项（增强版本，保持原有逻辑）
			OLED_Clear();
			
			OLED_ShowStringCentered(16, "Reset All", OLED_6X8_HALF);
			OLED_ShowStringCentered(28, "Reset Single", OLED_6X8_HALF);
			OLED_ShowStringCentered(40, "Back", OLED_6X8_HALF);
			
			// 高亮当前选中的行
			OLED_HighlightMenuLine(flag_change - 1, true);
			// 叠加右上角电量与低电提示
			OLED_DrawBatteryIconTopRight();
			OLED_BatteryLowNotifier_Update();
			
			OLED_Display();
			last_flag_change = flag_change;  // 更新记录
		}
		
		osDelay(10);  // 增加延时，减少刷新频率
	}
}

// 新增：角度速度选择菜单
int menu3_angle_speed(void)
{
	static uint8_t last_flag_change = 0;  // 记录上次的选择，避免重复刷新
	
	flag_change = 1;
	debug_change_state = 1;  // 设置状态为选择角度速度
	// 不重置参数值，使用调用前已设置的值（从Flash读取或默认值）
	debug_config_changed = false;
	
	OLED_Clear();
	OLED_Display();
	
	key_num = 0;

	while(1)
	{
	key_num = Key_GetEvent();
		if(key_num == 1 )
		{
			flag_change--;
			if(flag_change == 0 )
			{
				flag_change = 5; // 5个选项：角度、速度、开或关、保存、退出
			}
		}
		else if(key_num == 2 )
		{
			if(flag_change == 1) {
				// 选择角度
				debug_temp_angle = (debug_temp_angle % 3) + 1;
				debug_config_changed = true;
			}
			else if(flag_change == 2) {
				// 选择速度
				debug_temp_speed = (debug_temp_speed % 3) + 1;
				debug_config_changed = true;
			}
			else if(flag_change == 3) {
				// 选择开或关
				debug_open_or_not_flag = (debug_open_or_not_flag % 2) + 1;
				debug_config_changed = true;
			}
			else if(flag_change == 4) {
				// 保存配置
				debug_change_state = 2;
				return 1;  // 保存
			}
			else if(flag_change == 5) {
				// 退出不保存
				return 0;  // 退出
			}
		}
		else if(key_num == 3 )
		{
			flag_change++;
			if(flag_change > 5 )
			{
				 flag_change = 1;
			}
		}
		
		// 只有当选择发生变化时才刷新显示
		if (flag_change != last_flag_change || debug_config_changed) {
			// 显示配置界面（保持原有逻辑，添加视觉增强）
			OLED_Clear();
			
			// 显示配置项
			char config_display[50];
			
			// 角度配置 (三挡: 小/中/大)
			const char* angle_names[] = {"Small", "Medium", "Large"};
			sprintf(config_display, "Angle: %s", angle_names[debug_temp_angle - 1]);
			OLED_ShowStringCentered(16, config_display, OLED_6X8_HALF);
			
			// 速度配置  
			const char* speed_names[] = {"Slow", "Moderate", "Fast"};
			sprintf(config_display, "Speed: %s", speed_names[debug_temp_speed - 1]);
			OLED_ShowStringCentered(28, config_display, OLED_6X8_HALF);
			
			// 开关配置
			sprintf(config_display, "Auto Close: %s", (debug_open_or_not_flag == 1) ? "Yes" : "No");
			OLED_ShowStringCentered(40, config_display, OLED_6X8_HALF);
			
			// 操作选项
			if (flag_change == 4) {
				OLED_ShowStringCentered(52, "Save", OLED_6X8_HALF);
			} else if (flag_change == 5) {
				OLED_ShowStringCentered(52, "Exit", OLED_6X8_HALF);
			}
			
			// 高亮当前选择项
			OLED_HighlightMenuLine(flag_change - 1, true);
			// 叠加右上角电量与低电提示
			OLED_DrawBatteryIconTopRight();
			OLED_BatteryLowNotifier_Update();
			
			OLED_Display();
			last_flag_change = flag_change;  // 更新记录
			debug_config_changed = false;    // 重置配置变化标志
		}
		
		osDelay(10);
	}
}
// 隐藏菜单：门最大开度校准
void handle_Reset_menu(void)
{
	// 进入时发送AARE55
	HC15_SendMessage("AARE55");
	// 清屏并显示提示界面
	OLED_Clear();
	
	// 绘制装饰边框
	OLED_DrawRectangle(2, 2, 124, 60, OLED_UNFILLED);
	OLED_DrawRectangle(3, 3, 122, 58, OLED_UNFILLED);
	
	// 显示标题
	OLED_ShowStringCentered(8, "Door Calibration", OLED_6X8_HALF);
	
	// 绘制分隔线（使用OLED_DrawLine绘制水平线）
	OLED_DrawLine(8, 18, 120, 18);
	
	// 显示操作提示（使用更小的字体以适应屏幕）
	OLED_ShowStringCentered(24, "Please open door", OLED_6X8_HALF);
	OLED_ShowStringCentered(34, "to maximum angle", OLED_6X8_HALF);
	
	// 显示按键提示
	OLED_ShowStringCentered(48, "Press KEY to confirm", OLED_6X8_HALF);
	
	OLED_Update();
	
	// 等待任意按键
	while (1) {
	int key = Key_GetEvent();
		if (key != 0) {  // 任意按键都可以确认
			break;
		}
		osDelay(10);
	}
	
	// 发送AA0055
	HC15_SendMessage("AA0055");
	
	// 在成功界面前显示一个约10秒的阻塞式进度条
	Flash_ShowBlockingProgress(10000U);

	// 显示完成界面
	OLED_Clear();
	
	// 绘制成功提示框
	OLED_DrawRectangle(5, 5, 118, 54, OLED_UNFILLED);
	OLED_DrawRectangle(6, 6, 116, 52, OLED_UNFILLED);
	
	// 显示成功图标（居中的对勾符号）
	// 计算居中位置：屏幕宽度128，对勾宽度约14像素，居中x=57
	OLED_DrawLine(57, 22, 62, 27);  // 对勾左半部分
	OLED_DrawLine(62, 27, 70, 19);  // 对勾右半部分
	OLED_DrawLine(58, 23, 63, 28);  // 增加粗细度
	OLED_DrawLine(63, 28, 71, 20);  // 增加粗细度
	
	// 显示完成文字（更好的垂直居中）
	OLED_ShowStringCentered(38, "Calibration Complete!", OLED_6X8_HALF);
	
	OLED_Update();
	osDelay(2000);
	
	// 返回一级菜单
	OLED_Clear();
	OLED_Update();
}

// 新增：Else Mode二级菜单 - 包含勿扰模式和重置模式
int menu2_else_mode_with_return(void)
{
	static uint8_t last_flag_change = 0;  // 记录上次的选择，避免重复刷新
	
	flag_change = 1;
	last_flag_change = 0;  // 强制重置，确保初始显示
	
	// 立即显示初始菜单
	OLED_Clear();
	
	OLED_ShowStringCentered(16, "Do Not Disturb", OLED_6X8_HALF);
	OLED_ShowStringCentered(28, "Door Reset", OLED_6X8_HALF);
	OLED_ShowStringCentered(40, "Back", OLED_6X8_HALF);
			
	// 高亮当前选中的行
	OLED_HighlightMenuLine(flag_change - 1, true);
	// 叠加右上角电量与低电提示
	OLED_DrawBatteryIconTopRight();
	OLED_BatteryLowNotifier_Update();

	OLED_Display();
	last_flag_change = 1;  // 标记已显示
	
	while(1)
	{
	key_num = Key_GetEvent();
		if(key_num == 1 )
		{
			flag_change--;
			if(flag_change == 0 )
			{
				 flag_change = 3; // 三个选项：勿扰模式、重置模式、返回
			}
		}
		else if(key_num == 2 )
		{
			OLED_Clear();
			OLED_Display();
			if(flag_change == 3) {
				return 0; // 返回上一级
			}
			return flag_change;
		}
		else if(key_num == 3 )
		{
			flag_change++;
			if(flag_change > 3 )
			{
				 flag_change = 1;
			}
		}
		
		// 只有当选择发生变化时才刷新显示
		if (flag_change != last_flag_change) {
			// 显示菜单项
			OLED_Clear();
			
			OLED_ShowStringCentered(16, "Do Not Disturb", OLED_6X8_HALF);
			OLED_ShowStringCentered(28, "Door Reset", OLED_6X8_HALF);
			OLED_ShowStringCentered(40, "Back", OLED_6X8_HALF);
			
			// 高亮当前选中的行
			OLED_HighlightMenuLine(flag_change - 1, true);
			// 叠加右上角电量与低电提示
			OLED_DrawBatteryIconTopRight();
			OLED_BatteryLowNotifier_Update();
			
			OLED_Display();
			last_flag_change = flag_change;  // 更新记录
		}
		
		osDelay(10);  // 增加延时，减少刷新频率
	}
}

// 新增：处理Else Mode菜单选择
void handle_else_mode_menu(void)
{
	int choice = menu2_else_mode_with_return();
	if(choice == 0)
	{
		return; // 返回上一级
	} 
	else if(choice == 1) 
	{
		// 进入勿扰模式
		silent_do_not_disturb = true;  // 设置静默勿扰模式标志
		system_state = Do_not_disturb;  // 设置系统状态为勿扰模式
		OLED_Clear();
		OLED_Update();
	}
	else if(choice == 2)
	{
		// 进入门重置校准模式
		handle_Reset_menu();
	}
}

// 封装菜单处理函数
void handle_config_menu(void)
{
    // 显示配置开始状态 (带动画效果) 
    OLED_Clear();
    OLED_ScrollTextInCentered(15, "Radar Config", OLED_8X16_HALF, ANIMATION_SLIDE_DOWN, SCROLL_SPEED_FAST);
    osDelay(1000);
    
    // 设置用户ID为1
    selected_user_id = 1;
    
    // 先从Flash读取ID1的配置作为初始值
    user_config_t current_config;
    bool config_exists = Flash_LoadUserConfig(1, &current_config);
    
    if (!config_exists) {
        // Flash为空，使用默认配置
        Flash_GetDefaultUserConfig(&current_config, 1);
        OLED_Clear();
        OLED_ShowStringCentered(15, "Loading defaults...", OLED_6X8_HALF);
        osDelay(1000);
    } else {
        // 显示读取现有配置
        OLED_Clear();
        OLED_ShowStringCentered(15, "Loading config...", OLED_6X8_HALF);
        OLED_Update();
        osDelay(1000);
    }

	OLED_Clear();
    
    // 将当前配置设置为临时编辑值（显示初始值）
    debug_temp_angle = current_config.open_angle;
    debug_temp_speed = current_config.open_speed;
    debug_open_or_not_flag = current_config.open_or_not_flag;
    
    // 显示当前配置信息
    char config_info[64];
    sprintf(config_info, "Config ID: %d", selected_user_id);
    OLED_ShowStringCentered(35, config_info, OLED_6X8_HALF);
    OLED_Update();
    osDelay(1500);

    // 进入角度速度配置菜单
    int config_result = menu3_angle_speed();
    if (config_result == 1) {
        // 用户完成了配置，现在擦除Flash并写入新配置
        
        // 显示保存进度
        OLED_Clear();
        OLED_ShowStringCentered(15, "Saving config...", OLED_6X8_HALF);
        
        // 启动保存进度条动画
        enroll_progress_active = true;
        enroll_progress_start_time = HAL_GetTick();
        enroll_progress_duration = 2000;  // 2秒保存时长
        
        uint32_t save_start = HAL_GetTick();
        bool save_success = false;
        
        // 准备配置数据
        user_cfg_diy.user_id = selected_user_id;
        user_cfg_diy.open_angle = debug_temp_angle;
        user_cfg_diy.open_speed = debug_temp_speed;
        user_cfg_diy.open_or_not_flag = debug_open_or_not_flag;
        
        // 先擦除所有用户数据
        bool erase_success = Flash_EraseAllUserData();
        
        if (erase_success) {
            // 擦除成功，写入新配置
            // 由于已经擦除，直接使用简化的写入逻辑
            Flash_Unlock();
            
            // 计算地址（确保8字节对齐）
            uint32_t flash_address = FLASH_USER_BASE_ADDR + (user_cfg_diy.user_id * USER_CONFIG_FLASH_SIZE);
            flash_address = (flash_address + 7) & ~7;  // 向上对齐到8字节边界
            
            // 准备写入数据 + CRC
            user_config_t temp_cfg = user_cfg_diy;
            temp_cfg.crc = 0;  // 先清零CRC字段
            temp_cfg.crc = calculate_crc(&temp_cfg);
            
            // 直接写入数据（Flash已经被擦除）
            Flash_Status write_result = Flash_Write64BitAligned(flash_address, &temp_cfg, sizeof(user_config_t));
            
            Flash_Lock();
            
            save_success = (write_result == FLASH_OK);
            
            // 调试：验证写入是否成功
            if (save_success) {
                // 立即读取验证
                user_config_t verify_cfg;
                bool verify_result = Flash_LoadUserConfig(user_cfg_diy.user_id, &verify_cfg);
                if (!verify_result) {
                    save_success = false;  // 验证失败
                } else {
                    // 验证数据是否正确
                    if (verify_cfg.user_id != user_cfg_diy.user_id ||
                        verify_cfg.open_angle != user_cfg_diy.open_angle ||
                        verify_cfg.open_speed != user_cfg_diy.open_speed ||
                        verify_cfg.open_or_not_flag != user_cfg_diy.open_or_not_flag) {
                        save_success = false;  // 数据不匹配
                    }
                }
            }
        }
        
        // 显示保存进度条动画
        while ((HAL_GetTick() - save_start) < enroll_progress_duration) {
            if (enroll_progress_active) {
                uint32_t elapsed = HAL_GetTick() - enroll_progress_start_time;
                uint8_t progress = (elapsed * 100) / enroll_progress_duration;
                
                if (progress > 100) {
                    progress = 100;
                    enroll_progress_active = false;
                }
                
                // 清除进度区域并重新绘制
                OLED_ClearArea(10, 30, 108, 20);
                OLED_ShowProgressBar(10, 35, 108, progress, PROGRESS_SPEED_FAST);
                OLED_Update();
            }
            osDelay(50);
        }
        
        if (save_success) {
            // 显示保存成功
            OLED_Clear();
            OLED_ShowMessageCentered("Config Saved", "Successfully!");
            osDelay(2000);
            system_state = FACE_ENROLL_SUCCESS;
        } else {
            // 显示保存失败
            OLED_Clear();
            OLED_DrawRectangle(5, 5, 118, 54, OLED_UNFILLED);
            OLED_DrawRectangle(6, 6, 116, 52, OLED_UNFILLED);
            OLED_ShowStringCentered(23, "Save Failed", OLED_7X12_HALF);
            OLED_Update();
            osDelay(2000);
            system_state = FACE_ENROLL_FAIL;
        }
    } else {
        // 用户取消了配置
        system_state = FACE_ENROLL_FAIL;
    }
}


void handle_delete_menu(void)
{
	delete_num = menu2_delete_with_return();
	if(delete_num == 0)
	{
		return; // 返回上一级
	} 
	else if(delete_num == 1) 
	{

		Delete = true ;	
		osDelay(5);   

	}
	else if(delete_num == 2)
	{
		// 删除单个用户
		OLED_ShowMessageCentered("Reset Single", "Press any key");
	while(Key_GetEvent() == 0) { osDelay(5); }
	}
	
	// 初始化删除成功标志
	delete_success = false;
	
	if( Delete == true )
	{
		// 显示删除进度
		uint32_t delete_start = HAL_GetTick();
		uint32_t delete_timeout = 5000;  // 1秒超时
		
		FaceRec_ClearAllUsers();
		osDelay(100);
		
		// 显示删除进度条动画
		OLED_Clear();
		OLED_ShowStringCentered(15, "Resetting...", OLED_6X8_HALF);
		
		while ((HAL_GetTick() - delete_start) < delete_timeout)
		{
			// 计算并显示进度
			uint32_t elapsed = HAL_GetTick() - delete_start;
			uint8_t progress = (elapsed * 100) / delete_timeout;
			
			// 清除进度区域并重新绘制
			OLED_ClearArea(10, 30, 108, 20);
			OLED_ShowProgressBar(10, 35, 108, progress, PROGRESS_SPEED_FAST);
			
			FaceRec_ClearAllUsers();
			osDelay(100);
			// 完全事件驱动：只在有数据时处理，否则让出CPU
			if (FaceRec_HasDataAvailable()) {
				FaceRec_Process();  // 处理接收到的数据
			} else {
				// 没有数据时让出CPU，减少占用
				osDelay(5);  // 5ms延时，平衡响应性和CPU占用
			}
			if (FaceRec_IsDeleteSuccess())
			{
				delete_success = true;
				// 显示完成进度条
				OLED_ClearArea(10, 30, 108, 20);
				OLED_ShowProgressBar(10, 35, 108, 100, PROGRESS_SPEED_FAST);
				break;
			}
		}
	}
	
	// 只有当执行了删除操作时才设置状态
	if (Delete == true)
	{
		if (delete_success)
		{
				system_state = FACE_DELETE_SUCCESS;
		}
		else
		{
				system_state = FACE_DELETE_FAIL;
		}
	}
}

// 主菜单处理函数
void process_main_menu(int menu_choice)
{

	switch(menu_choice)
	{
		case 1: // config - 雷达参数配置
			handle_config_menu();
			break;
		case 2: // else mode - 其他模式（勿扰模式和重置模式）
			handle_else_mode_menu();
			break;
		case 3: // back - 返回
			OLED_Clear();
			system_state = SYSTEM_IDLE;
			all_control = false;
			break;
	}
}
void Flash_Task(void * argument)
{
    for (;;)
    {
    	if(system_state != Do_not_disturb && lora_rx_flag==1)
    	{
    		HC15_SendMessage("AARI55");
    		lora_rx_flag=0;
    		osDelay(10);
    	}
		osDelay(10);

        switch (system_state)
        {
			case Do_not_disturb:
				HC15_SendMessage("AA0055");
				osDelay(10);
				static uint32_t pir_start = 0;
				if(lora_rx_flag==1)
				{
					HC15_SendMessage("AARF55");
					osDelay(10);
					lora_rx_flag = 0;                   // 清除LoRa接收标志
				}
				// 检查长按按键3退出勿扰模式（无论是静默还是非静默模式）
				key_num = Key_GetEvent();
				if (key_num == 1 || key_num == 2 || key_num == 3) {  // 长按按键3
					silent_do_not_disturb = false;  // 清除静默标志
					system_state = SYSTEM_IDLE;  // 退出勿扰模式---
					OLED_Clear();
					OLED_Update();
					break;
				}
				
				// 如果是静默勿扰模式，不显示任何内容
				if (silent_do_not_disturb) {
					OLED_Clear();
					OLED_Update();
					break;
				}
				
				// 非静默勿扰模式，保持原有的PIR显示逻辑
				if(HAL_GPIO_ReadPin(PIR_INPUT_GPIO_Port, PIR_INPUT_Pin) == GPIO_PIN_SET)
				{
					pir_start = HAL_GetTick();
				}
				if((HAL_GetTick() - pir_start) < 5000)
				{
					OLED_Clear();
					OLED_DrawRectangle(5, 5, 118, 54, OLED_UNFILLED);
					OLED_DrawRectangle(6, 6, 116, 52, OLED_UNFILLED);
					char disturb_info[35];
					sprintf(disturb_info, "Do not disturb!");
					OLED_ShowStringCentered(23, disturb_info, OLED_7X12_HALF);
					OLED_Update();
				}
				else
				{
					OLED_Clear();
					OLED_Update();
				}
				break;
            case SYSTEM_IDLE:
            {
				static uint32_t idle_start = 0;
				if(idle_start == 0)
				{
					idle_start = HAL_GetTick();
				}
				if(HAL_GetTick() - idle_start > 2000)
				{
					idle_start = 0;
                    pre_Sleep_Flag = 1;

					XY_MB06BA_SendATCommand("AT+DISCONN=1");
                    osDelay(10);
                    XY_MB06BA_SendATCommand("AT+DISCONN=0");
                    osDelay(10);
					XY_MB06BA_SendATCommand("AT+DISCONN=1");
                    osDelay(10);
                    XY_MB06BA_SendATCommand("AT+DISCONN=0");
                    osDelay(10);
					HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_SET);	
					HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);	
					OLED_Clear();
					OLED_Update();
					/* 确保NMOS处于关闭状态（PC2为本项目默认门极引脚） */
					HAL_GPIO_WritePin(GPIOC, GPIO_PIN_2, GPIO_PIN_RESET);
					PowerMgmt_SetLowPowerMode(1);
					osDelay(1000);
				}
				OLED_Clear();
				OLED_Update();
				osDelay(50);
                break;
            }

            case FACE_VERIFYING:
            {
                (void)HAL_GetTick(); // 避免未使用变量警告
                osDelay(50);  // 增加延时，减少刷新频率
                break;
            }
            case FACE_VERIFY_SUCCESS:
                break;

            case FACE_VERIFY_FAIL:
				OLED_Clear();
				OLED_DrawRectangle(5, 5, 118, 54, OLED_UNFILLED);
				OLED_DrawRectangle(6, 6, 116, 52, OLED_UNFILLED);
				OLED_Update();
                OLED_ShowMessageCentered("Radar Failed", "No detection");
                osDelay(1500);
                system_state = SYSTEM_IDLE;
                all_control = false;
                break;

            case FACE_ENROLL_SUCCESS:
				OLED_Clear();
				OLED_DrawRectangle(5, 5, 118, 54, OLED_UNFILLED);
				OLED_DrawRectangle(6, 6, 116, 52, OLED_UNFILLED);
				OLED_Update();
                OLED_ShowMessageCentered("Config Success", "Settings saved");
                osDelay(1500);
                system_state = MENU_ACTIVE;
                break;

            case FACE_ENROLL_FAIL:

                system_state = MENU_ACTIVE;
                break;

            case FACE_DELETE_SUCCESS:
				OLED_Clear();
				OLED_DrawRectangle(5, 5, 118, 54, OLED_UNFILLED);
				OLED_DrawRectangle(6, 6, 116, 52, OLED_UNFILLED);
				OLED_Update();
                OLED_ShowMessageCentered("Reset Success", "Data cleared");
                osDelay(1500);
                system_state = MENU_ACTIVE;
                Delete = false;
                break;

            case FACE_DELETE_FAIL:
				OLED_Clear();
				OLED_DrawRectangle(5, 5, 118, 54, OLED_UNFILLED);
				OLED_DrawRectangle(6, 6, 116, 52, OLED_UNFILLED);
				OLED_Update();
                OLED_ShowMessageCentered("Reset Failed", "Try again");
                osDelay(1500);
                system_state = MENU_ACTIVE;
                Delete = false;
                break;

            case MENU_ACTIVE:
            {
				face_enroll_in_progress = true;
                int menu_choice = menu1();
				if(system_state != Do_not_disturb)
				{
					process_main_menu(menu_choice);
                    if(system_state != Do_not_disturb)
					{
						system_state = SYSTEM_IDLE;
					}
				}
                face_enroll_in_progress = false;
                break;
            }

            default:
                OLED_ShowMessageCentered("System Error", "Unknown state");
                osDelay(1000);
                system_state = SYSTEM_IDLE;
                break;
        }

        osDelay(1);
    }
}

// 用户配置结构体已在 Flash.h 中定义

// 计算CRC校验
static uint8_t calculate_crc(const user_config_t *cfg) {
    uint8_t crc = 0;
    const uint8_t *data = (const uint8_t*)cfg;
    for (int i = 0; i < sizeof(user_config_t) - 1; i++) {
        crc ^= data[i];
    }
    return crc;
}

// ===== 蓝牙地址存储相关功能 =====

// 蓝牙地址存储结构体
typedef struct {
    uint8_t mac_address[6];     // 6字节MAC地址
    uint8_t is_valid;           // 有效性标志：0x55表示有效，其他值表示无效
    uint8_t reserved[9];        // 保留字段，确保16字节对齐
    uint8_t crc;               // CRC校验
} ble_address_storage_t;

#define BLE_ADDRESS_FLASH_ADDR    0x0803F800    // 蓝牙地址独立存储区域(2KB)，与用户数据区域完全分离
#define BLE_ADDRESS_VALID_FLAG    0x55          // 有效标志

// 计算蓝牙地址存储的CRC校验
static uint8_t calculate_ble_address_crc(const ble_address_storage_t *addr_storage) {
    uint8_t crc = 0;
    const uint8_t *data = (const uint8_t*)addr_storage;
    for (int i = 0; i < sizeof(ble_address_storage_t) - 1; i++) {
        crc ^= data[i];
    }
    return crc;
}

bool Flash_LoadUserConfig(uint16_t user_id, user_config_t *cfg) {
    if (!cfg) return false;
    if (user_id >= MAX_USER_CONFIG_COUNT) return false;

    // 计算地址（确保8字节对齐）
    uint32_t flash_address = FLASH_USER_BASE_ADDR + (user_id * USER_CONFIG_FLASH_SIZE);
    flash_address = (flash_address + 7) & ~7;  // 向上对齐到8字节边界
    
    if (flash_address >= FLASH_USER_END_ADDR) return false;

    // 读取数据（按64位检查）
    uint64_t *raw_data = (uint64_t*)flash_address;

    // 检查是否为空（擦除状态）
    bool is_empty = true;
    uint32_t words_to_check = (sizeof(user_config_t) + 7) / 8;  // 向上取整到8字节
    for (uint32_t i = 0; i < words_to_check; i++) {
        if (raw_data[i] != 0xFFFFFFFFFFFFFFFFULL) {
            is_empty = false;
            break;
        }
    }
    if (is_empty) return false;

    // 拷贝数据
    memcpy(cfg, raw_data, sizeof(user_config_t));

    // CRC 校验
    uint8_t crc_check = calculate_crc(cfg);
    if (crc_check != cfg->crc) {
        // CRC校验失败，可能数据损坏
        return false;
    }

    return true;
}

// 专门用于64位对齐写入的函数
static Flash_Status Flash_Write64BitAligned(uint32_t address, const void* data, uint32_t size) {
    // 确保地址8字节对齐
    if (address & 0x7) {
        return FLASH_ERROR;
    }
    
    // 创建64位对齐的缓冲区
    uint64_t aligned_buffer[16];  // 最多128字节，足够存储用户配置
    memset(aligned_buffer, 0xFF, sizeof(aligned_buffer));  // 填充0xFF
    memcpy(aligned_buffer, data, size);
    
    // 计算需要写入的64位字数
    uint32_t words_to_write = (size + 7) / 8;  // 向上取整到8字节边界
    
    // 按64位写入
    for (uint32_t i = 0; i < words_to_write; i++) {
        HAL_StatusTypeDef status = HAL_FLASH_Program(
            FLASH_TYPEPROGRAM_DOUBLEWORD, 
            address + i * 8, 
            aligned_buffer[i]
        );
        if (status != HAL_OK) {
            return FLASH_ERROR;
        }
    }
    
    return FLASH_OK;
}

void Flash_SaveUserConfig(const user_config_t *cfg) {
    if (!cfg) return;

    // 检查ID范围
    if (cfg->user_id >= MAX_USER_CONFIG_COUNT) return;

    // 解锁Flash
    Flash_Unlock();

    // 计算地址（确保8字节对齐）
    uint32_t flash_address = FLASH_USER_BASE_ADDR + (cfg->user_id * USER_CONFIG_FLASH_SIZE);
    flash_address = (flash_address + 7) & ~7;  // 向上对齐到8字节边界
    
    if (flash_address >= FLASH_USER_END_ADDR) {
        Flash_Lock();
        return;
    }

    // 准备写入数据 + CRC
    user_config_t temp_cfg = *cfg;
    temp_cfg.crc = 0;  // 先清零CRC字段，避免计算时包含旧值
    temp_cfg.crc = calculate_crc(&temp_cfg);

    // 计算页的起始地址
    uint32_t page_start_addr = flash_address & ~(0x800 - 1);  // 对齐到2KB边界
    
    // 检查页是否需要擦除（只要页内有任何数据，就需要擦除重写）
    bool need_erase = false;
    uint64_t *page_check_addr = (uint64_t*)page_start_addr;
    for (int i = 0; i < 0x800 / 8; i++) { // 遍历整个页 (2KB / 8字节)
        if (page_check_addr[i] != 0xFFFFFFFFFFFFFFFFULL) {
            need_erase = true;
            break;
        }
    }
    
    // 如果需要擦除，先备份页中的其他用户数据，然后擦除页，再恢复其他用户数据
    if (need_erase) {
        // 定义页缓冲区（64位对齐）
        static uint64_t page_buffer[0x800 / 8];  // 2KB页缓冲区，按64位对齐
        
        // 读取整个页的数据
        memcpy(page_buffer, (void*)page_start_addr, 0x800);
        
        // 擦除页
        if (Flash_ErasePage(page_start_addr) != FLASH_OK) {
            Flash_Lock();
            return;
        }
        
        // 更新缓冲区中当前用户的数据
        uint32_t offset_in_page = flash_address - page_start_addr;
        memcpy((uint8_t*)page_buffer + offset_in_page, &temp_cfg, sizeof(user_config_t));
        
        // 将整个页的数据写回Flash（按64位写入）
        for (int i = 0; i < 0x800 / 8; i++) {
            uint32_t write_addr = page_start_addr + i * 8;
            HAL_StatusTypeDef status = HAL_FLASH_Program(FLASH_TYPEPROGRAM_DOUBLEWORD, write_addr, page_buffer[i]);
            if (status != HAL_OK) {
                Flash_Lock();
                return;
            }
        }
    } else {
        // 如果当前位置为空，直接写入数据（使用64位对齐写入）
        if (Flash_Write64BitAligned(flash_address, &temp_cfg, sizeof(user_config_t)) != FLASH_OK) {
            Flash_Lock();
            return;
        }
    }

    Flash_Lock();
}

/**
 * @brief 擦除所有用户配置数据
 * @return true: 擦除成功, false: 擦除失败
 */
bool Flash_EraseAllUserData(void)
{
    // 解锁Flash
    Flash_Unlock();
    
    // 计算需要擦除的页数
    // 用户数据区域：0x0803C000 到 0x0803F800 (14KB)
    // 每页2KB，共7页
    uint32_t start_page_addr = FLASH_USER_BASE_ADDR;
    uint32_t end_addr = FLASH_USER_END_ADDR;
    uint32_t page_size = 0x800;  // 2KB per page
    
    bool erase_success = true;
    
    // 逐页擦除
    for (uint32_t page_addr = start_page_addr; page_addr < end_addr; page_addr += page_size) {
        if (Flash_ErasePage(page_addr) != FLASH_OK) {
            erase_success = false;
            break;
        }
    }
    
    Flash_Lock();
    return erase_success;
}

/**
 * @brief 获取默认用户配置
 * @param cfg 配置结构体指针
 * @param user_id 用户ID
 */
void Flash_GetDefaultUserConfig(user_config_t *cfg, uint16_t user_id)
{
    if (!cfg) return;
    
    // 设置默认配置值
    cfg->user_id = user_id;
    cfg->open_angle = 1;        // 默认角度：90度 (0=90度, 1=120度, 2=180度)
    cfg->open_speed = 1;        // 默认速度：中速 (0=慢速, 1=中速, 2=快速)
    cfg->open_or_not_flag = 1;  // 默认开门
    
    // 清零保留字段
    memset(cfg->reserved, 0, sizeof(cfg->reserved));
    
    // 计算CRC
    cfg->crc = 0;
    cfg->crc = calculate_crc(cfg);
}

/**
 * @brief 从Flash读取蓝牙地址
 * @param mac_address 6字节MAC地址缓冲区
 * @return bool true: 读取成功且地址有效, false: 读取失败或地址无效
 */
bool Flash_LoadBLEAddress(uint8_t *mac_address) {
    if (!mac_address) return false;

    // 读取存储结构
    ble_address_storage_t *stored_addr = (ble_address_storage_t*)BLE_ADDRESS_FLASH_ADDR;
    
    // 检查是否为空（擦除状态）
    uint64_t *raw_data = (uint64_t*)stored_addr;
    bool is_empty = true;
    uint32_t words_to_check = (sizeof(ble_address_storage_t) + 7) / 8;
    for (uint32_t i = 0; i < words_to_check; i++) {
        if (raw_data[i] != 0xFFFFFFFFFFFFFFFFULL) {
            is_empty = false;
            break;
        }
    }
    if (is_empty) return false;

    // 拷贝数据到临时结构
    ble_address_storage_t temp_storage;
    memcpy(&temp_storage, stored_addr, sizeof(ble_address_storage_t));

    // CRC校验
    uint8_t crc_check = calculate_ble_address_crc(&temp_storage);
    if (crc_check != temp_storage.crc) {
        return false;  // CRC校验失败
    }

    // 检查有效标志
    if (temp_storage.is_valid != BLE_ADDRESS_VALID_FLAG) {
        return false;  // 地址无效
    }

    // 检查地址是否全0或全F
    bool all_zero = true;
    bool all_ff = true;
    for (int i = 0; i < 6; i++) {
        if (temp_storage.mac_address[i] != 0x00) all_zero = false;
        if (temp_storage.mac_address[i] != 0xFF) all_ff = false;
    }
    if (all_zero || all_ff) {
        return false;  // 无效地址
    }

    // 拷贝有效地址
    memcpy(mac_address, temp_storage.mac_address, 6);
    return true;
}

/**
 * @brief 向Flash保存蓝牙地址
 * @param mac_address 6字节MAC地址
 * @return bool true: 保存成功, false: 保存失败
 */
bool Flash_SaveBLEAddress(const uint8_t *mac_address) {
    if (!mac_address) return false;

    // 检查地址有效性
    bool all_zero = true;
    bool all_ff = true;
    for (int i = 0; i < 6; i++) {
        if (mac_address[i] != 0x00) all_zero = false;
        if (mac_address[i] != 0xFF) all_ff = false;
    }
    if (all_zero || all_ff) {
        return false;  // 无效地址
    }

    // 解锁Flash
    Flash_Unlock();
    
    // 擦除存储页面（2KB页）
    uint32_t page_addr = BLE_ADDRESS_FLASH_ADDR & ~(0x800 - 1);
    if (Flash_ErasePage(page_addr) != FLASH_OK) {
        Flash_Lock();
        return false;
    }

    // 准备存储结构
    ble_address_storage_t addr_storage = {0};
    memcpy(addr_storage.mac_address, mac_address, 6);
    addr_storage.is_valid = BLE_ADDRESS_VALID_FLAG;
    memset(addr_storage.reserved, 0, sizeof(addr_storage.reserved));
    
    // 计算并设置CRC
    addr_storage.crc = 0;
    addr_storage.crc = calculate_ble_address_crc(&addr_storage);

    // 写入Flash（使用64位对齐写入）
    Flash_Status write_result = Flash_Write64BitAligned(BLE_ADDRESS_FLASH_ADDR, &addr_storage, sizeof(ble_address_storage_t));
    
    Flash_Lock();
    
    if (write_result != FLASH_OK) {
        return false;
    }

    // 验证写入是否成功
    uint8_t verify_addr[6];
    return Flash_LoadBLEAddress(verify_addr) && (memcmp(verify_addr, mac_address, 6) == 0);
}

/**
 * @brief 清空Flash中的蓝牙地址
 * @return bool true: 清空成功, false: 清空失败
 */
bool Flash_ClearBLEAddress(void) {
    // 解锁Flash
    Flash_Unlock();
    
    // 擦除存储页面（2KB页）
    uint32_t page_addr = BLE_ADDRESS_FLASH_ADDR & ~(0x800 - 1);
    Flash_Status erase_result = Flash_ErasePage(page_addr);
    
    Flash_Lock();
    
    return (erase_result == FLASH_OK);
}

//测试git 测试效果

```

