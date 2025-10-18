#include "main.h"
#include "gpio.h"
#include "freertos.h"
#include "cmsis_os.h"
#include "motor.h"
#include "usart.h"
#include "yaw.h"
#include "flash_storage.h"
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <stdint.h>
#include "low_power.h"
#include "xy_mb06ba.h"  // 添加蓝牙模块头文件
#include "f_radar.h"
#include "gyro_yaw_processor.h"
#include "gyro_calib_storage.h"  // 新增：陀螺仪校准偏置Flash存取


/*
 * Control task (Else_Task):
 * - Parse LoRa commands (2128 forward, 2222 reverse, 1515 forward)
 * - Handle AA00 command: turns on motor for human detection, sends open_control for 5 seconds,
 *   keeps motor on while:
 *   * Messages are being received, OR
 *   * Door is being physically pushed/pulled (ahead_flag/back_flag active)
 * - Manage execution flags and segment motor speed by yaw delta
 * - Coordinate with Auto_Check (calibration/limit procedure)
 *
 * NOTE: Comments improved for clarity. Logic and code unchanged.
 */
//test branch intern1


// Task and execution flags
bool check_flag = false ;
bool initialized = false, waitingForReverse = false;  
bool commandReceived = false, commandExecuted = false, commandExecuted_r = false;
bool yaw_zero_set = false, yaw_zero_set_r = false;
bool stop_set = false;
static bool stall_check_initialized = false;
uint8_t motor_runing_flag=0;
uint8_t motor_runing_flag_r=0;
uint8_t close_or_not_flag=0;
uint8_t closing_inpurrt=0;
    
// 解析环形缓冲，若有新值则更新全局变量
int16_t current_raw = 0;


// AA00 command flags
bool aa00_motor_enabled = false;
uint32_t last_message_time = 0; // 最近一次收到 AA00 或进入运动的时间
uint32_t move_start = 0;
#define MESSAGE_TIMEOUT_MS 100  // 10s 无 AA00 且未运动则下电
#define Motor_P 40



// Yaw tracking
float  diff;            // forward: |yaw - yaw_zero|
float  diff_r;          // reverse: |yaw - yaw_zero|
float yaw_zero = 0.0f;  // yaw origin

// Yaw stall detection variables
static float yaw_stall_check_start = 0.0f;
static uint32_t yaw_stall_timer = 0;
static bool yaw_stall_detected = false;


int16_t target_speed;
uint8_t Speed_Level_Lora=3;
uint8_t Angle_Level_Lora=1;
int16_t Speed_from_Lora=2000;
int16_t face_control_flag=0;
uint8_t close_flag=0;

extern uint8_t usart_rx_buffer[10];  
extern uint8_t lora_rx_buf[8]; 
extern volatile uint8_t lora_rx_flag ;
extern char incoming[8] ;  
extern float yaw_offset, yaw_raw, yaw, yaw_zero, diff_sumh, diff_sump_last, diff_sumup;
extern bool received_message ;
extern uint8_t motor_cmd[10];
extern bool ahead_flag ;
extern bool back_flag ;
extern uint8_t open_control[10];  // 开环控制命令数组
extern uint8_t speed_control[10];  // 速度环控制命令数组
extern FRadar_Handle s_fradar;
extern LSM6DSV16X_Handle imu_handle;  // LSM6DSV16X传感器句柄
void send_data(uint8_t *data);    // 发送数据到电机函数

// 函数声明
bool Yaw_Stall_Check(void);

void Else_Task(void const * argument)
{
    lora_rx_flag = 0;
    rpm0_Stop(); 

    Flash_Result_t result;
    float saved_diff_sumup;
    bool saved_check_flag;
    
    // 初始化并尝试从Flash读取数据
    result = Flash_Storage_Init();
    if (result == FLASH_RESULT_OK) {
        result = Flash_Storage_Read(&saved_diff_sumup, &saved_check_flag);
        if (result == FLASH_RESULT_OK) {
            // 恢复保存的数据
            extern float diff_sumup;
            extern bool check_flag;
            diff_sumup = saved_diff_sumup;
            check_flag = saved_check_flag;
        }
    }
    if(check_flag)
    {
        HAL_GPIO_WritePin(SIGNAL_ENABLE_PORT, SIGNAL_ENABLE_PIN, GPIO_PIN_RESET);
    }
    for(;;)
    {
        static GPIO_EdgeType_t detected_edge;
        static GPIO_PinState last_pb6_state = GPIO_PIN_RESET;
        static uint32_t last_pb6_time = 0;
        static uint8_t pb6_flag = 0;
        Motor_SetBusCurrentSlot(2);
        (void)Motor_TryReadBusCurrent(&current_raw); // 内部已更新全局原始与换算电流

        // 检查蓝牙指令 
        XY_MB06BA_CheckAndParseCommands();
        if(!check_flag )
        {
            if(lora_rx_flag)
            {
                // trigger auto range/limit check when a frame arrives
                Auto_Check();
                close_flag=0;
                memset(lora_rx_buf, 0, sizeof(lora_rx_buf));
                Wake_time=HAL_GetTick();
            }	 
        }
        else if( check_flag == true)
        {

            static uint8_t diff_threshold_init = 0;
            static uint8_t Motor_Init = 0;
            static uint8_t diff_threshold_init_r = 0;
            static uint8_t Motor_Init_r = 0;

            if(motor_runing_flag == 1 || motor_runing_flag_r == 1)
                Wake_time=HAL_GetTick();

            if(HAL_GetTick()-Wake_time>15000 && fabsf(yaw)<10)
            {
                HAL_GPIO_WritePin(SIGNAL_ENABLE_PORT, SIGNAL_ENABLE_PIN, GPIO_PIN_RESET);
                // HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_RESET); 
                HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_RESET);
                HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);

                osDelay(10);
                JY61P_UART_Enter_Sleep();
                osDelay(10);
                XY_MB06BA_SendATCommand("AT+DISCONN=1");
                osDelay(10);
                XY_MB06BA_SendATCommand("AT+DISCONN=0");
                osDelay(10);
                XY_MB06BA_SendATCommand("AT+DISCONN=1");
                osDelay(10);
                XY_MB06BA_SendATCommand("AT+DISCONN=0");

                HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_SET);
                HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET);
                LSM6DSV16X_AllSleep(&imu_handle);
                osDelay(10);
                FRadar_SetDistanceAndSave(&s_fradar, 512); // 设置雷达距离阈值为2000mm并保存到非易失存储器
                LowPower_SetSleepFlag(1);
                osDelay(1000);
            }
            else if(HAL_GetTick()-Wake_time>15000)
            {
                Wake_time=HAL_GetTick();
                motor_runing_flag_r=1;
            }


            // new LoRa frame arrives: parse command key
            if (lora_rx_flag)
            {

                lora_rx_flag = 0;
                
                // 更新消息接收时间 (用于AA00超时检测)
                if (aa00_motor_enabled) {
                    last_message_time = HAL_GetTick();
                }
                
                // 解析LoRa命令 - 检测4字节命令(命令缓冲区)
                if (lora_rx_buf[0] == 'A' && lora_rx_buf[1] == 'A')
                {
                    // 检测AA00命令 - 开启电机并保持开启状态
                    if (lora_rx_buf[2] == '0' && lora_rx_buf[3] == '0')
                    {
                        // AA00命令：电机上电
                        HAL_GPIO_WritePin(SIGNAL_ENABLE_PORT, SIGNAL_ENABLE_PIN, GPIO_PIN_SET);
                        aa00_motor_enabled = true;
                        last_message_time = HAL_GetTick();
                        // 只做上电保持，不再启动开环阶段
                    }
                    else
                    {
                        // 其他AA命令的处理
                        // 将lora_rx_buf[2]和lora_rx_buf[3]转换为数字
                        // 假设接收的是ASCII字符，需要转换为对应的数值
                        uint8_t speed_char = lora_rx_buf[2];
                        uint8_t angle_char = lora_rx_buf[3];
                        
                        // 方法1: 如果接收的是ASCII数字字符 (例如: '1', '2', '3')
                        if (speed_char >= '1' && speed_char <= '3') {
                            Speed_Level_Lora = speed_char - '0';  // 转换为0-9的数值
                            face_control_flag=1;
                            commandExecuted = true;
                            motor_runing_flag=1;
                            closing_inpurrt=1;
                        }
                        
                        if (angle_char >= '1' && angle_char <= '3') {
                            Angle_Level_Lora = angle_char - '0';  // 转换为0-9的数值
                        }
                        switch (Speed_Level_Lora)
                        {
                        case 1:
                            Speed_from_Lora = 600;
                            break;
                        case 2:
                            Speed_from_Lora = 1200;
                            break;
                        case 3:
                            Speed_from_Lora = 2000;
                            break;
                        default:
                            Speed_from_Lora = 1500;
                            break;
                        }

                        if(speed_char == 'O' && angle_char == 'F')
                        {
                            close_flag=1;
                        }
                        if(speed_char == 'R' && angle_char == 'E')
                        {
                            lora_rx_flag=0;
                            check_flag=0;
                        }
                    }
                }
                memset(lora_rx_buf, 0, sizeof(lora_rx_buf));
            }



            if (((commandExecuted || ahead_flag == true) && fabs(diff_sumup-yaw)>2 && yaw<diff_sumup) || motor_runing_flag == 1) 
            {  		
                Wake_time=HAL_GetTick();
                motor_runing_flag=1;
                if(Motor_Init == 0)
                {
                    HAL_GPIO_WritePin(SIGNAL_ENABLE_PORT, SIGNAL_ENABLE_PIN, GPIO_PIN_SET);
                    move_start = HAL_GetTick();
                    osDelay(10);
                    g_motor_bus_current_A=0;
                    Motor_Init=1;
                    stall_check_initialized = false; // 重置停滞检测状态
                }

                // 根据角度等级设置除数：1级=最小角度(/3), 2级=中等角度(/2), 3级=最大角度(/1)
                float angle_divisor;
                switch(Angle_Level_Lora) {
                    case 1: angle_divisor = 3.0f; break;  // 最小角度
                    case 2: angle_divisor = 2.0f; break;  // 中等角度
                    case 3: angle_divisor = 1.0f; break;  // 最大角度
                    default: angle_divisor = 2.0f; break; // 默认中等角度
                }

                float threshold = (diff_sumup / angle_divisor);

                if(face_control_flag == 0)
                {
                    threshold=diff_sumup;
                }
                
                static uint8_t speed_control_Init_flag=0;

                if(speed_control_Init_flag == 0)
                {
                    send_data(speed_control);
                    osDelay(10);
                    speed_control_Init_flag=1;
                }

                int16_t speed=Motor_P*(threshold-yaw);

                if(speed>Speed_from_Lora)
                {
                    speed=Speed_from_Lora;
                }
                else if(speed<-Speed_from_Lora)
                {
                    speed=-Speed_from_Lora;
                }

                motor_drive_cmd(0x01, speed, 20, 0, motor_cmd);   

                // 检测是否到达目标位置或yaw值停滞
                if (fabs(threshold-yaw)<5 || fabs(diff_sumup-yaw)<5 || Yaw_Stall_Check() || yaw > diff_sumup ) 
                {  
                    rpm0_Stop();
                    osDelay(10);
                    close_or_not_flag=0;
            
                    motor_runing_flag=0;
                    ahead_flag = false;
                    back_flag = false;
                    face_control_flag=0;
                    commandExecuted = false;  
                    yaw_zero_set = false;     
                    stop_set = false;
                    diff_threshold_init=0;
                    Motor_Init=0;
                    speed_control_Init_flag=0;

                    HAL_GPIO_WritePin(SIGNAL_ENABLE_PORT, SIGNAL_ENABLE_PIN, GPIO_PIN_RESET);
                    closing_inpurrt=0;
                    if(close_flag == 1)
                    {
                        commandExecuted_r=1;
                        motor_runing_flag_r=1;
                        close_flag=0;
                    }
                }
            }
            else
            {
                ahead_flag = false;
                commandExecuted = false;  
                yaw_zero_set = false;     
                diff_threshold_init=0;
                Motor_Init=0;
                if(close_flag == 1)
                {
                    commandExecuted_r=1;
                    motor_runing_flag_r=1;
                    close_flag=0;
                }
            }
            
            
            if (((commandExecuted_r ||  back_flag  == true) && fabs(yaw)>2 && yaw>0 )|| motor_runing_flag_r == 1)
            {
                Wake_time=HAL_GetTick();
                motor_runing_flag_r=1;
                if(Motor_Init_r == 0)
                {
                    HAL_GPIO_WritePin(SIGNAL_ENABLE_PORT, SIGNAL_ENABLE_PIN, GPIO_PIN_SET);
                    move_start = HAL_GetTick();
                    osDelay(10);
                    Motor_Init_r=1;
                    g_motor_bus_current_A=0;
                    stall_check_initialized = false; // 重置停滞检测状态
                }

                float threshold = 0;
                
                static uint8_t speed_control_Init_flag_r=0;

                if(speed_control_Init_flag_r == 0)
                {
                    send_data(speed_control);
                    osDelay(10);
                    speed_control_Init_flag_r=1;
                }

                int16_t speed=Motor_P*(threshold-(yaw+3));

                if(speed>Speed_from_Lora)
                {
                    speed=Speed_from_Lora;
                }
                else if(speed<-Speed_from_Lora)
                {
                    speed=-Speed_from_Lora;
                }

                motor_drive_cmd(0x01, speed, 20, 0, motor_cmd);   

                uint8_t is_collision = 0;
                // 检测是否到达目标位置或yaw值停滞
                if ((fabs(yaw)<5 || (is_collision=Yaw_Stall_Check()) || yaw < 0) || closing_inpurrt==1)
                {  
                    // stall_check_initialized = false; // 重置检测状态
                    if(is_collision==0 && closing_inpurrt==0)
                    {
                        motor_drive_cmd(0x01, -1000, 5, 0, motor_cmd);   
                        osDelay(1000);
                    }
                    HAL_GPIO_WritePin(SIGNAL_ENABLE_PORT, SIGNAL_ENABLE_PIN, GPIO_PIN_RESET); 
                    motor_runing_flag_r=0;
                    back_flag = false;
                    ahead_flag = false;
                    face_control_flag=0;
                    commandExecuted_r = false;  
                    yaw_zero_set_r = false;     
                    stop_set = false;
                    diff_threshold_init_r=0;
                    Motor_Init_r=0;
                    speed_control_Init_flag_r=0;
                    close_flag=0;

                    osDelay(100);


                    if(is_collision==0  && closing_inpurrt==0)
                    {
                        close_or_not_flag=1;
                        HAL_GPIO_WritePin(SIGNAL_ENABLE_PORT, SIGNAL_ENABLE_PIN, GPIO_PIN_RESET);
                        // HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_RESET); 
                        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_RESET);
                        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);

                        osDelay(10);
                        JY61P_UART_Enter_Sleep();
                        osDelay(10);
                        XY_MB06BA_SendATCommand("AT+DISCONN=1");
                        osDelay(10);
                        XY_MB06BA_SendATCommand("AT+DISCONN=0");
                        osDelay(10);
                        XY_MB06BA_SendATCommand("AT+DISCONN=1");
                        osDelay(10);
                        XY_MB06BA_SendATCommand("AT+DISCONN=0");
                        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_SET);
                        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET);
                        LSM6DSV16X_AllSleep(&imu_handle);
                        osDelay(10);
                        FRadar_SetDistanceAndSave(&s_fradar, 512);
                        LowPower_SetSleepFlag(1);
                        while(JY61P_UART_Reset_Yaw() != HAL_OK)
                        {
                            osDelay(10);
                        }
                    }
                    if(closing_inpurrt==1)
                    {
                        motor_runing_flag=1;
                        Motor_Init=0;
                        closing_inpurrt=0;
                    }
                }
            } 
            else
            {
                back_flag = false;
                commandExecuted_r = false;  
                yaw_zero_set_r = false;     
                diff_threshold_init_r=0;
                Motor_Init_r=0;
            }
        }


        osDelay(10);

        /* ---------------- AA00 保持与超时管理逻辑 ----------------
         * 收到 AA00 -> 上电并置 aa00_motor_enabled=true, 记录 last_message_time。
         * 若 10s 内未再次收到 AA00 且 机构未进入运动阶段 -> 下电。
         * 若进入运动阶段(任一运动标志为真) -> 视作仍在使用，刷新 last_message_time 防止下电。
         * 已删除开环阶段逻辑，仅保留简单上/下电控制。
         */
        if (aa00_motor_enabled) {
            uint32_t now = HAL_GetTick();
            bool moving = (motor_runing_flag || motor_runing_flag_r || ahead_flag || back_flag);

            // 运动阶段: 重置超时基准，保持供电
            if (moving) {
                last_message_time = now;  // 重置超时计时
            } else {
                // 未运动: 检查是否超时
                if (now - last_message_time > MESSAGE_TIMEOUT_MS) {
                    HAL_GPIO_WritePin(SIGNAL_ENABLE_PORT, SIGNAL_ENABLE_PIN, GPIO_PIN_RESET);
                    aa00_motor_enabled = false;
                }
            }
        }

        // 检测PB6双边沿变化（带防抖）
        if(GPIO_CheckEdge(GPIOB, GPIO_PIN_6, &last_pb6_state, &last_pb6_time, &detected_edge) && motor_runing_flag == 0 && motor_runing_flag_r == 0)
        {
            // 检测到任何边沿变化（上升沿或下降沿）
            if(detected_edge == GPIO_EDGE_RISING || detected_edge == GPIO_EDGE_FALLING)
            {
                pb6_flag++;
                if(pb6_flag>=1)
                {
                    pb6_flag=0;
                    motor_runing_flag=1;
                }
            }
        }
    }

}

/**
 * @brief 检测yaw值在1秒内变化是否超过3度或角度增量方向频繁变化或运动方向异常
 * @retval true: yaw值在1秒内变化不超过3度(停滞检测)或角度增量方向变化超过2次或运动方向异常
 * @retval false: yaw值正常变化
 * @description 仿照Auto_Check函数，检测电机运行时yaw值是否停滞或振荡或运动方向异常
 */
bool Yaw_Stall_Check(void)
{
    static float last_yaw = 0.0f;
    static float last_yaw_increment = 0.0f;
    static uint8_t direction_change_count = 0;
    static float last_yaw_abs = 0.0f;
    static uint8_t motion_direction_error_count = 0;
    static float A_Limit = 0.8f;

    if(HAL_GetTick()-move_start<1500) // 电机启动后1.5秒内不检测
        return false;

    // if(fabsf(g_motor_bus_current_A)>A_Limit)
    // {
    //     return true;    
    // }

    // 初始化检测
    if (!stall_check_initialized) {
        yaw_stall_check_start = yaw;
        yaw_stall_timer = HAL_GetTick();
        last_yaw = yaw;
        last_yaw_increment = 0.0f;
        direction_change_count = 0;
        last_yaw_abs = fabsf(yaw);
        motion_direction_error_count = 0;
        stall_check_initialized = true;
        yaw_stall_detected = false;
        return false;
    }
    
    // 计算当前yaw绝对值
    float current_yaw_abs = fabsf(yaw);
    
    // 检测运动方向异常
    // motor_runing_flag为1时，如果当前时刻yaw绝对值比上一时刻小则记一次
    if (motor_runing_flag == 1) {
        if (current_yaw_abs < last_yaw_abs && fabsf(current_yaw_abs - last_yaw_abs) > 0.01f) {
            motion_direction_error_count++;
        }
    }
    // motor_runing_flag_r为1时，如果当前时刻yaw角绝对值比上一时刻大记一次
    else if (motor_runing_flag_r == 1) {
        if (current_yaw_abs > last_yaw_abs && fabsf(current_yaw_abs - last_yaw_abs) > 0.01f) {
            motion_direction_error_count++;
        }
    }
    
    // 如果运动方向错误计数大于等于1次，返回true
    if (motion_direction_error_count >= 1) {
        yaw_stall_detected = true;
        stall_check_initialized = false; // 重置检测状态
        return true;
    }
    
    // 计算当前角度增量
    float current_yaw_increment = yaw - last_yaw;
    
    // 检测角度增量方向变化
    if (fabsf(current_yaw_increment) > 0.01f && fabsf(last_yaw_increment) > 0.01f) {
        // 判断增量方向是否相反（符号不同）
        if ((current_yaw_increment > 0 && last_yaw_increment < 0) || 
            (current_yaw_increment < 0 && last_yaw_increment > 0)) {
            direction_change_count++;
            
            // 如果方向变化超过2次，认为是振荡，返回true
            if (direction_change_count >= 2) {
                yaw_stall_detected = true;
                stall_check_initialized = false; // 重置检测状态
                return true;
            }
        }
    }
    
    // 更新上一次的yaw值、增量和绝对值
    last_yaw = yaw;
    last_yaw_increment = current_yaw_increment;
    last_yaw_abs = current_yaw_abs;
    
    // 检测yaw值变化
    float yaw_change = fabsf(yaw - yaw_stall_check_start);
    uint32_t elapsed_time = HAL_GetTick() - yaw_stall_timer;
    
    // 如果yaw值变化超过0.2度，重置检测
    if (yaw_change > 0.1f) {
        yaw_stall_check_start = yaw;
        yaw_stall_timer = HAL_GetTick();
        direction_change_count = 0; // 重置方向变化计数
        motion_direction_error_count = 0; // 重置运动方向错误计数
        yaw_stall_detected = false;
        return false;
    }
    
    // 如果1秒内yaw值变化不超过3度，认为停滞
    if (elapsed_time >= 1500 && yaw_change <= 0.1f) {
        yaw_stall_detected = true;
        stall_check_initialized = false; // 重置检测状态
        return true;
    }
    
    return false;
}
