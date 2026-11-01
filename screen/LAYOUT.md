# Screen layout

Generated from `UI/xindi_800_480.HMI` by `tools/hmi_dump.py --markdown`. Do not edit by hand.

"Reports" is the widget number the screen sends in a touch event (`65 <page> <widget> FF FF FF`). Labels are the Chinese defaults in the layout; the screen replaces them per language.

## Pages

| Page | Name |
| --- | --- |
| 0 | logo |
| 1 | restart |
| 2 | shutdown |
| 3 | main |
| 4 | file_list |
| 5 | preview |
| 6 | preview_pop_1 |
| 7 | preview_pop_2 |
| 8 | syntony |
| 9 | syntony_move |
| 10 | bed_calibrate |
| 11 | pre_calibrate |
| 12 | calibrate_scr |
| 13 | calibrate_move |
| 14 | auto_level |
| 15 | auto_move |
| 16 | zoffset |
| 17 | printing |
| 18 | print_kb |
| 19 | print_zoffset |
| 20 | print_finish |
| 21 | language |
| 22 | wifi |
| 23 | wifi_kb |
| 24 | wifi_connect |
| 25 | wifi_saving |
| 26 | wifi_success |
| 27 | wifi_fail |
| 28 | show_qr |
| 29 | system_ok |
| 30 | reset |
| 31 | sleep_mode |
| 32 | update |
| 33 | more |
| 34 | service |
| 35 | control |
| 36 | control_kb |
| 37 | pre_load |
| 38 | pre_unload |
| 39 | pre_heat |
| 40 | unload |
| 41 | load |
| 42 | move_pop_1 |
| 43 | screen_sleep |
| 44 | detect_error |
| 45 | gcode_error |
| 46 | update_success |
| 47 | updating |
| 48 | update_finish |
| 49 | print_no_fil |
| 50 | print_no_fil2 |
| 51 | print_log_s |
| 52 | print_log_f |
| 53 | print_stop |
| 54 | move_pop_2 |
| 55 | print_stopping |
| 56 | resume_print |
| 57 | memory_warning |
| 58 | control_setfan |
| 59 | syntony_finish |
| 60 | bedcal_finish |
| 61 | auto_finish |
| 62 | network |
| 63 | server_set |
| 64 | search_server |
| 65 | online_update |
| 66 | offline_update |
| 67 | installing |
| 68 | btn_conflict |
| 69 | language_2 |
| 70 | low_temp |
| 71 | load_2 |
| 72 | load_finish |
| 73 | auto_warning |
| 74 | cal_warning |
| 75 | re_printing |
| 76 | open_language1 |
| 77 | open_language2 |
| 78 | open_skip_pop |
| 79 | open_unpack1 |
| 80 | open_unpack2 |
| 81 | open_unpack3 |
| 82 | open_unpack4 |
| 83 | open_load1 |
| 84 | open_load2 |
| 85 | open_load3 |
| 86 | open_load4 |
| 87 | open_finish |
| 88 | connect_set |
| 89 | account_list |
| 90 | add_account |
| 91 | reset_account |
| 92 | account_kb |
| 93 | account_pop |
| 94 | more_pop |
| 95 | tool_select |
| 96 | dry |
| 97 | dry_prepare |
| 98 | dry_tips |
| 99 | dry_select |
| 100 | drying |
| 101 | dry_finish |
| 102 | debug |
| 103 | dry_warn1 |
| 104 | dry_warn2 |
| 105 | user_info |
| 106 | network_test |
| 107 | user_exit |
| 108 | connect_server |
| 109 | server_success |
| 110 | server_fail |
| 111 | forget_pwd |
| 112 | bed_heat_rules |
| 113 | zero_box_page |
| 114 | one_box_page |
| 115 | multi_box_page |
| 116 | user_guide |
| 117 | slot_params |
| 118 | vendor_set |
| 119 | filament_set |
| 120 | color_set |
| 121 | mc_print_set |
| 122 | unconnect_pop |
| 123 | vendor_pop |
| 124 | box_error_pop |
| 125 | data_pop |
| 126 | no_fila_pop |
| 127 | load_step1 |
| 128 | load_step2 |
| 129 | box_unlink_pop |
| 130 | box_link_pop |
| 131 | box_update_pop |
| 132 | load_error_pop |
| 133 | box_setting |
| 134 | fila_not_match |
| 135 | box_drying |
| 136 | drying_insp |
| 137 | page0 |

## 3 main

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 3 | b3 | button |  | 330,10 460x379 |
| 0 | b0 | button |  | 200,16 120x144 |
| 2 | b2 | button |  | 200,288 120x97 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 102 | b33 | button |  | 16,400 140x80 |
| 1 | b1 | button |  | 200,176 120x97 |

## 4 file_list

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 8 | b8 | button |  | 702,80 82x80 |
| 9 | b9 | button |  | 702,172 82x102 |
| 10 | b10 | button |  | 702,282 82x102 |
| 0 | b0 | button |  | 16,80 332x96 |
| 1 | b1 | button |  | 356,80 332x96 |
| 2 | b2 | button |  | 16,184 332x96 |
| 3 | b3 | button |  | 356,184 332x96 |
| 4 | b4 | button |  | 16,288 332x96 |
| 5 | b5 | button |  | 356,288 332x96 |
| 6 | b6 | button | 本地文件 | 15,0 201x64 |
| 7 | b7 | button | U盘文件 | 231,0 201x63 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 5 preview

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button |  | 30,304 114x64 |
| 1 | b1 | button |  | 159,304 114x64 |
| 2 | b2 | button |  | 320,304 448x64 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 3 | b3 | button |  | 320,224 448x64 |
| 4 | b4 | button |  | 319,147 448x64 |

## 6 preview_pop_1

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 168,310 224x64 |
| 1 | b1 | button | 不再提示 | 408,310 224x64 |

## 7 preview_pop_2

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 168,310 224x64 |
| 1 | b1 | button | 不再提示 | 408,310 224x64 |

## 8 syntony

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 3 | b3 | button |  | 412,303 166x64 |
| 4 | b4 | button |  | 220,303 166x64 |

## 9 syntony_move

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 10 bed_calibrate

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 3 | b3 | button |  | 416,302 160x64 |
| 8 | b8 | button |  | 223,302 160x64 |

## 11 pre_calibrate

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 3 | b3 | button | 下一步 | 608,304 160x64 |
| 4 | b4 | button |  | 344,32 152x76 |
| 5 | b5 | button |  | 496,32 152x76 |
| 6 | b6 | button |  | 344,108 152x76 |
| 7 | b7 | button |  | 496,108 152x76 |
| 8 | b8 | button |  | 664,32 104x72 |
| 9 | b9 | button |  | 664,112 104x72 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 12 calibrate_scr

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 3 | b3 | button | 下一步 | 608,304 160x64 |

## 13 calibrate_move

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 14 auto_level

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 6 | b6 | button |  | 362,304 160x64 |

## 15 auto_move

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 16 zoffset

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button | 自动调平 | 16,480 220x64 |
| 1 | b1 | button | 平台校准 | 252,480 220x64 |
| 2 | b2 | button | 共振补偿 | 488,480 220x64 |

## 17 printing

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 102 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 528,304 112x64 |
| 1 | b1 | button |  | 656,304 112x64 |
| 2 | b2 | button |  | 16,320 122x64 |
| 3 | b3 | button |  | 150,320 122x64 |
| 4 | b4 | button |  | 16,232 120x72 |
| 5 | b5 | button |  | 152,232 120x72 |

## 18 print_kb

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 528,304 112x64 |
| 1 | b1 | button |  | 656,304 112x64 |
| 2, 12 | b2 | button |  | 16,320 122x64 |
| 3, 12 | b3 | button |  | 150,320 122x64 |
| 12 | b6 | button |  | 412,109 76x99 |
| 4 | b4 | button |  | 16,232 120x72 |
| 5 | b5 | button |  | 152,232 120x72 |
| 13 | b13 | button |  | 24,224 240x72 |

## 19 print_zoffset

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 528,304 112x64 |
| 1 | b1 | button |  | 656,304 112x64 |
| 2 | b2 | button |  | 16,320 122x64 |
| 3 | b3 | button |  | 150,320 122x64 |
| 6 | b6 | button |  | 31,138 85x62 |
| 7 | b7 | button |  | 116,138 84x62 |
| 8 | b8 | button |  | 200,138 84x62 |
| 9 | b9 | button |  | 284,138 84x62 |
| 10 | b10 | button |  | 384,32 96x76 |
| 11 | b11 | button |  | 384,124 96x76 |
| 12 | b4 | button |  | 16,232 120x72 |
| 5 | b5 | button |  | 152,232 120x72 |

## 20 print_finish

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 完成 | 472,310 160x64 |

## 21 language

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 22 wifi

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 11 | wifi1 | button |  | 300,24 400x64 |
| 12 | wifi2 | button |  | 300,96 400x64 |
| 13 | wifi3 | button |  | 300,168 400x64 |
| 14 | wifi4 | button |  | 300,240 400x64 |
| 6 | b6 | button |  | 706,24 70x64 |
| 7 | b7 | button |  | 706,104 70x88 |
| 8 | b8 | button |  | 706,209 70x88 |
| 10 | b10 | button |  | 706,313 70x64 |
| 15 | wifi5 | button |  | 300,312 400x64 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 17 | b17 | button |  | 624,22 70x64 |

## 23 wifi_kb

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b26 | button |  | 24,84 100x60 |

## 24 wifi_connect

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | tm0 | timer |  | None,None NonexNone |

## 26 wifi_success

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 27 wifi_fail

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 28 show_qr

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 36 | b36 | button |  | 488,400 140x80 |
| 34 | b34 | button |  | 172,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 9 | b9 | button |  | 672,312 104x64 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 10 | b10 | button |  | 672,25 104x64 |

## 29 system_ok

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 6 | b6 | button | 导出系统日志 | 306,240 190x136 |
| 7 | b7 | button |  | 510,240 266x64 |
| 8 | b8 | button |  | 510,312 266x64 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |

## 30 reset

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 6 | b6 | button | 导出系统日志 | 306,240 190x136 |
| 7 | b7 | button |  | 510,240 266x64 |
| 8 | b8 | button |  | 510,312 266x64 |

## 31 sleep_mode

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |

## 32 update

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 6 | b6 | button | 离线更新 | 306,312 226x64 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 7 | b7 | button | 在线更新 | 549,312 226x64 |

## 33 more

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 6 | b6 | button | 售后信息 | 314,32 220x64 |
| 8 | b8 | button | 恢复出厂设置 | 314,112 290x64 |
| 9, 11 | b9 | button |  | 314,272 454x64 |
| 10 | b10 | button |  | 314,192 454x64 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 7 | b7 | button |  | 619,112 148x64 |
| 3 | b3 | button | 熄屏设置 | 548,32 220x64 |

## 34 service

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |

## 35 control

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 24,24 92x64 |
| 1 | b1 | button |  | 24,121 92x64 |
| 2 | b2 | button |  | 24,217 92x64 |
| 3 | b3 | button |  | 134,24 66x64 |
| 3 | b4 | button |  | 134,121 66x64 |
| 3 | b5 | button |  | 134,217 66x64 |
| 6 | b6 | button |  | 255,311 130x64 |
| 7 | b7 | button |  | 386,311 130x64 |
| 8 | b8 | button |  | 516,311 130x64 |
| 9 | b9 | button |  | 646,311 130x64 |
| 10 | b10 | button |  | 356,124 80x80 |
| 11 | b11 | button |  | 548,124 72x80 |
| 13 | b13 | button |  | 636,24 140x136 |
| 14 | b14 | button |  | 320,24 152x80 |
| 16 | b16 | button |  | 256,88 80x152 |
| 17 | b17 | button |  | 456,88 80x152 |
| 15 | b15 | button |  | 320,224 152x80 |
| 18 | b18 | button |  | 548,24 72x86 |
| 19 | b19 | button |  | 548,218 72x86 |
| 20 | b20 | button |  | 712,168 64x64 |
| 21 | b21 | button |  | 712,240 64x64 |
| 22 | b22 | button |  | 16,304 216x80 |

## 36 control_kb

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 25 | b6 | button |  | 684,147 84x222 |
| 0 | b0 | button |  | 24,24 92x64 |
| 1 | b1 | button |  | 24,121 92x64 |
| 2 | b2 | button |  | 24,217 92x64 |
| 22 | b22 | button |  | 16,304 216x80 |

## 37 pre_load

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 24,24 92x64 |
| 1 | b1 | button |  | 24,121 92x64 |
| 2 | b2 | button |  | 24,217 92x64 |
| 3 | b3 | button |  | 134,24 66x64 |
| 3 | b4 | button |  | 134,121 66x64 |
| 3 | b5 | button |  | 134,217 66x64 |
| 22 | b22 | button |  | 16,304 216x80 |
| 9 | b9 | button | 返回 | 524,304 244x64 |
| 10 | b10 | button | 下一步 | 264,304 244x64 |

## 38 pre_unload

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 24,24 92x64 |
| 1 | b1 | button |  | 24,121 92x64 |
| 2 | b2 | button |  | 24,217 92x64 |
| 3 | b3 | button |  | 134,24 66x64 |
| 3 | b4 | button |  | 134,121 66x64 |
| 3 | b5 | button |  | 134,217 66x64 |
| 22 | b22 | button |  | 16,304 216x80 |
| 9 | b9 | button | 返回 | 524,304 244x64 |
| 10 | b10 | button | 下一步 | 264,304 244x64 |

## 39 pre_heat

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 6 | b6 | button |  | 334,135 122x64 |
| 7 | b7 | button |  | 456,135 120x64 |
| 8 | b8 | button |  | 576,135 120x64 |
| 9 | b9 | button | 返回 | 524,304 244x64 |
| 10 | b10 | button | 下一步 | 264,304 244x64 |
| 0 | b0 | button |  | 24,24 92x64 |
| 1 | b1 | button |  | 24,121 92x64 |
| 2 | b2 | button |  | 24,217 92x64 |
| 3 | b3 | button |  | 134,24 66x64 |
| 3 | b4 | button |  | 134,121 66x64 |
| 3 | b5 | button |  | 134,217 66x64 |
| 22 | b22 | button |  | 16,304 216x80 |

## 40 unload

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 9 | b9 | button | 装载耗材 | 264,304 244x64 |
| 10 | b10 | button | 完成 | 524,304 244x64 |
| 0 | b0 | button |  | 24,24 92x64 |
| 1 | b1 | button |  | 24,121 92x64 |
| 2 | b2 | button |  | 24,217 92x64 |
| 3 | b3 | button |  | 134,24 66x64 |
| 3 | b4 | button |  | 134,121 66x64 |
| 3 | b5 | button |  | 134,217 66x64 |
| 22 | b22 | button |  | 16,304 216x80 |

## 41 load

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 24,24 92x64 |
| 1 | b1 | button |  | 24,121 92x64 |
| 2 | b2 | button |  | 24,217 92x64 |
| 3 | b3 | button |  | 134,24 66x64 |
| 3 | b4 | button |  | 134,121 66x64 |
| 3 | b5 | button |  | 134,217 66x64 |
| 22 | b22 | button |  | 16,304 216x80 |

## 42 move_pop_1

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 是 | 167,311 222x60 |
| 1 | b1 | button | 否 | 410,312 222x60 |

## 43 screen_sleep

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | touch | gmov |  | None,None NonexNone |

## 44 detect_error

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 45 gcode_error

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 46 update_success

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 49 print_no_fil

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 50 print_no_fil2

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 51 print_log_s

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 52 print_log_f

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 53 print_stop

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 是 | 170,312 222x60 |
| 1 | b1 | button | 否 | 407,312 222x60 |

## 54 move_pop_2

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 56 resume_print

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 2 | resume_print | page |  | 0,0 800x480 |
| 0 | b0 | button | 是 | 170,312 222x60 |
| 1 | b1 | button | 否 | 407,312 222x60 |

## 57 memory_warning

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 485,308 150x68 |

## 58 control_setfan

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 36 | b36 | button |  | 488,400 140x80 |
| 34 | b34 | button |  | 172,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 6 | b6 | button |  | 328,68 82x132 |
| 7 | b7 | button |  | 511,68 82x132 |
| 8 | b8 | button |  | 695,68 82x132 |
| 9 | h0 | slider |  | 256,68 70x308 |
| 9 | h1 | slider |  | 439,68 70x308 |
| 9 | h2 | slider |  | 622,68 70x308 |
| 0 | b0 | button |  | 24,24 92x64 |
| 1 | b1 | button |  | 24,121 92x64 |
| 2 | b2 | button |  | 24,217 92x64 |
| 3 | b3 | button |  | 134,24 66x64 |
| 3 | b4 | button |  | 134,121 66x64 |
| 3 | b5 | button |  | 134,217 66x64 |
| 22 | b22 | button |  | 16,304 216x80 |

## 59 syntony_finish

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 3 | b3 | button | 确认 | 320,304 160x64 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 60 bedcal_finish

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 3 | b3 | button | 确认 | 320,304 160x64 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 61 auto_finish

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 3 | b3 | button | 确认 | 320,304 160x64 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 62 network

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 36 | b36 | button |  | 488,400 140x80 |
| 34 | b34 | button |  | 172,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 6 | b6 | button |  | 670,86 106x70 |
| 7 | b7 | button |  | 670,156 106x70 |
| 8 | b8 | button | WiFi连接 | 302,232 232x70 |
| 9 | b9 | button | Fluidd账户 | 546,232 232x70 |
| 10 | b10 | button |  | 304,160 356x64 |
| 20 | b20 | button | 客户端 | 546,308 232x70 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 21 | b21 | button | 服务器 | 302,308 232x70 |
| 22 | b22 | button |  | 556,88 104x60 |

## 63 server_set

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 36 | b36 | button |  | 488,400 140x80 |
| 34 | b34 | button |  | 172,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 6 | b6 | button |  | 706,24 70x64 |
| 9 | b9 | button |  | 706,312 70x64 |
| 7 | b7 | button |  | 706,104 70x88 |
| 8 | b8 | button |  | 706,208 70x88 |
| 10 | server1 | button |  | 306,24 392x64 |
| 11 | server2 | button |  | 306,96 392x64 |
| 12 | server3 | button |  | 306,168 392x64 |
| 13 | server4 | button |  | 306,240 392x64 |
| 14 | server5 | button |  | 306,312 392x64 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |

## 65 online_update

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 6 | b6 | button | 确定 | 306,312 226x64 |
| 7 | b7 | button | 返回 | 549,312 226x64 |

## 66 offline_update

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 6 | b6 | button | 确定 | 306,312 226x64 |
| 7 | b7 | button | 返回 | 549,312 226x64 |

## 68 btn_conflict

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 69 language_2

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 70 low_temp

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 71 load_2

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 24,24 92x64 |
| 1 | b1 | button |  | 24,121 92x64 |
| 2 | b2 | button |  | 24,217 92x64 |
| 3 | b3 | button |  | 134,24 66x64 |
| 3 | b4 | button |  | 134,121 66x64 |
| 3 | b5 | button |  | 134,217 66x64 |
| 22 | b22 | button |  | 16,304 216x80 |

## 72 load_finish

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 24,24 92x64 |
| 1 | b1 | button |  | 24,121 92x64 |
| 2 | b2 | button |  | 24,217 92x64 |
| 3 | b3 | button |  | 134,24 66x64 |
| 3 | b4 | button |  | 134,121 66x64 |
| 3 | b5 | button |  | 134,217 66x64 |
| 22 | b22 | button |  | 16,304 216x80 |
| 9 | b9 | button | 重试 | 264,304 244x64 |
| 10 | b10 | button | 完成 | 524,304 244x64 |

## 73 auto_warning

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 74 cal_warning

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button |  | 432,224 336x64 |
| 1 | b1 | button | 返回 | 432,304 160x64 |
| 2 | b2 | button | 下一步 | 608,304 160x64 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 76 open_language1

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 跳过 | 440,400 160x64 |
| 1 | b1 | button | 下一步 | 616,400 160x64 |

## 77 open_language2

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 跳过 | 440,400 160x64 |
| 1 | b1 | button | 下一步 | 616,400 160x64 |

## 78 open_skip_pop

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 是 | 170,312 222x60 |
| 1 | b1 | button | 否 | 407,312 222x60 |

## 79 open_unpack1

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button |  | 616,400 160x64 |

## 80 open_unpack2

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button |  | 616,400 160x64 |

## 81 open_unpack3

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 下一步 | 616,400 160x64 |

## 82 open_unpack4

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | tm0 | timer |  | None,None NonexNone |

## 83 open_load1

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button |  | 616,400 160x64 |

## 84 open_load2

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button |  | 616,400 160x64 |

## 85 open_load3

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button |  | 616,400 160x64 |

## 86 open_load4

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 下一步 | 616,400 160x64 |
| 1 | b1 | button | 进料 | 440,400 160x64 |

## 87 open_finish

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 完成 | 320,368 160x64 |

## 88 connect_set

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 6 | b6 | button |  | 672,312 104x64 |
| 9 | b9 | button | 服务器 | 306,311 350x64 |
| 8 | b8 | button | Fluidd账户管理 | 306,233 470x64 |
| 7 | b7 | button |  | 672,25 104x64 |

## 89 account_list

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 25,105 328x84 |
| 1 | b1 | button |  | 25,198 328x84 |
| 2 | b2 | button |  | 25,291 328x84 |
| 3 | b3 | button |  | 361,105 328x84 |
| 4 | b4 | button |  | 361,198 328x84 |
| 5 | b5 | button |  | 361,291 328x84 |
| 6 | b6 | button |  | 288,105 64x84 |
| 7 | b7 | button |  | 288,198 64x84 |
| 8 | b8 | button |  | 288,291 64x84 |
| 9 | b9 | button |  | 624,105 64x84 |
| 10 | b10 | button |  | 624,198 64x84 |
| 11 | b11 | button |  | 624,291 64x84 |
| 12 | b12 | button | 添加账户 | 24,24 512x64 |
| 13 | b13 | button | 重置密码 | 800,24 248x64 |
| 14 | b14 | button |  | 552,24 104x64 |
| 15 | b15 | button |  | 672,24 104x64 |
| 16 | b16 | button |  | 706,104 70x128 |
| 17 | b17 | button |  | 706,248 70x128 |

## 90 add_account

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 9 | b9 | button |  | 306,232 470x64 |
| 8 | b8 | button |  | 306,112 470x64 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 7 | b7 | button | 确定 | 306,312 228x64 |
| 6 | b6 | button | 取消 | 548,312 228x64 |

## 91 reset_account

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 10 | b7 | button | 确认 | 306,312 228x64 |
| 6 | b6 | button | 取消 | 548,312 228x64 |
| 9 | b9 | button |  | 306,232 470x64 |
| 8 | b8 | button |  | 306,112 470x64 |

## 92 account_kb

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0, 1 | b26 | button |  | 24,84 100x60 |

## 93 account_pop

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 是 | 170,312 222x60 |
| 1 | b1 | button | 否 | 407,312 222x60 |

## 94 more_pop

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确认 | 168,310 224x64 |
| 1 | b1 | button | 取消 | 408,310 224x64 |

## 95 tool_select

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button | 平台校准 | 530,60 204x126 |
| 1 | b1 | button | 自动调平 | 65,60 204x126 |
| 2 | b2 | button | 共振补偿 | 298,60 204x126 |
| 3 | b3 | button | 耗材烘干 | 65,212 204x126 |
| 4 | b4 | button | BOX烘干 | 300,210 204x126 |

## 96 dry

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 1 | b1 | button |  | 220,303 166x64 |
| 0 | b0 | button |  | 412,303 166x64 |

## 97 dry_prepare

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |

## 98 dry_tips

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button | 退出 | 390,300 166x68 |
| 1 | b1 | button | 开始 | 567,300 166x68 |
| 2 | b2 | button |  | 30,30 290x68 |

## 99 dry_select

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button |  | 30,30 290x68 |
| 1 | b1 | button |  | 348,24 348x62 |
| 2 | b2 | button |  | 348,96 348x62 |
| 3 | b3 | button |  | 348,168 348x62 |
| 4 | b4 | button |  | 348,240 348x62 |
| 5 | b5 | button |  | 348,312 348x62 |
| 6 | b6 | button |  | 710,24 66x168 |
| 7 | b7 | button |  | 710,206 66x168 |

## 100 drying

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button | 中止 | 480,300 164x68 |

## 101 dry_finish

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 0 | b0 | button | 确认 | 316,300 166x68 |

## 102 debug

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 退出 | 350,400 100x50 |
| 1 | b1 | button | 检测耗材宽度 | 280,80 160x30 |

## 103 dry_warn1

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 104 dry_warn2

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 105 user_info

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 36 | b36 | button |  | 488,400 140x80 |
| 34 | b34 | button |  | 172,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 9 | b9 | button |  | 672,312 104x64 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 8 | b8 | button | 退出账号 | 306,312 352x64 |
| 10 | b10 | button |  | 672,25 104x64 |

## 106 network_test

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 36 | b36 | button |  | 488,400 140x80 |
| 34 | b34 | button |  | 172,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 0 | b0 | button |  | 0,16 282x74 |
| 1 | b1 | button |  | 0,90 282x74 |
| 2 | b2 | button |  | 0,164 282x74 |
| 4 | b4 | button |  | 0,238 282x74 |
| 5 | b5 | button |  | 0,312 282x74 |
| 9 | b9 | button |  | 672,312 104x64 |

## 107 user_exit

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确认 | 168,310 224x64 |
| 1 | b1 | button | 取消 | 408,310 224x64 |

## 109 server_success

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 110 server_fail

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 111 forget_pwd

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确认 | 168,310 224x64 |
| 1 | b1 | button | 取消 | 408,310 224x64 |

## 112 bed_heat_rules

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 113 zero_box_page

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | 退出 | 24,312 160x64 |
| 2 | b1 | button | 指南 | 264,312 160x64 |
| 3 | b2 | button | 进料 | 440,312 160x64 |
| 4 | b3 | button | 退料 | 616,312 160x64 |
| 5 | b4 | button |  | 604,192 104x64 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 6 | b5 | button |  | 24,208 104x56 |
| 7 | b6 | button |  | 24,24 104x184 |

## 114 one_box_page

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 19 | b21 | button |  | 705,89 63x55 |
| 18 | b19 | button |  | 640,89 63x55 |
| 17 | b22 | button |  | 705,32 63x55 |
| 16 | b18 | button |  | 640,32 63x55 |
| 1 | b0 | button |  | 24,312 115x64 |
| 2 | b1 | button | 卸载 | 264,312 160x64 |
| 3 | b2 | button | 进料 | 440,312 160x64 |
| 4 | b3 | button | 退料 | 616,312 160x64 |
| 5 | b4 | button |  | 24,208 104x56 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 6 | b5 | button |  | 208,208 104x56 |
| 7 | b6 | button |  | 314,208 104x56 |
| 8 | b7 | button |  | 420,208 104x56 |
| 9 | b8 | button |  | 526,208 104x56 |
| 10 | b9 | button |  | 24,24 104x184 |
| 11 | b10 | button |  | 208,24 104x184 |
| 12 | b11 | button |  | 314,24 104x184 |
| 13 | b12 | button |  | 420,24 104x184 |
| 14 | b13 | button |  | 526,24 104x184 |
| 71 | b14 | button |  | 229,26 65x55 |
| 72 | b15 | button |  | 334,26 65x55 |
| 73 | b16 | button |  | 441,26 65x55 |
| 74 | b17 | button |  | 547,26 65x55 |
| 20 | b23 | button |  | 139,310 115x64 |
| 21 | b20 | button |  | 642,188 128x72 |
| 42 | b41 | button |  | 216,120 80x64 |
| 47 | b46 | button |  | 216,192 80x64 |
| 48 | b47 | button |  | 304,192 80x64 |
| 43 | b42 | button |  | 304,120 80x64 |
| 44 | b43 | button |  | 392,120 80x64 |
| 49 | b48 | button |  | 392,192 80x64 |
| 50 | b49 | button |  | 480,192 80x64 |
| 45 | b44 | button |  | 480,120 80x64 |
| 46 | b45 | button |  | 568,120 80x64 |
| 51 | b50 | button |  | 568,192 80x64 |
| 40 | b39 | button |  | 660,32 108x72 |
| 41 | b40 | button |  | 660,120 108x136 |
| 24 | b24 | button |  | 611,265 170x44 |

## 115 multi_box_page

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | 退出 | 24,312 160x64 |
| 2 | b1 | button | 卸载 | 264,312 160x64 |
| 3 | b2 | button | 进料 | 440,312 160x64 |
| 4 | b3 | button | 退料 | 616,312 160x64 |
| 5 | b4 | button |  | 24,208 104x56 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 6 | b5 | button |  | 208,208 104x56 |
| 7 | b6 | button |  | 314,208 104x56 |
| 8 | b7 | button |  | 420,208 104x56 |
| 9 | b8 | button |  | 526,208 104x56 |
| 10 | b9 | button |  | 24,24 104x184 |
| 11 | b10 | button |  | 208,24 104x184 |
| 12 | b11 | button |  | 314,24 104x184 |
| 13 | b12 | button |  | 420,24 104x184 |
| 14 | b13 | button |  | 526,24 104x184 |
| 16 | b15 | button |  | 640,32 63x55 |
| 17 | b16 | button |  | 705,32 63x55 |
| 18 | b17 | button |  | 640,89 63x55 |
| 19 | b18 | button |  | 705,89 63x55 |
| 21 | b20 | button |  | 640,152 128x72 |
| 42 | b41 | button |  | 216,120 80x64 |
| 43 | b42 | button |  | 304,120 80x64 |
| 44 | b43 | button |  | 392,120 80x64 |
| 45 | b44 | button |  | 480,120 80x64 |
| 46 | b45 | button |  | 568,120 80x64 |
| 47 | b46 | button |  | 216,192 80x64 |
| 48 | b47 | button |  | 304,192 80x64 |
| 49 | b48 | button |  | 392,192 80x64 |
| 50 | b49 | button |  | 480,192 80x64 |
| 51 | b50 | button |  | 568,192 80x64 |
| 40 | b39 | button |  | 660,32 108x72 |
| 41 | b40 | button |  | 660,120 108x136 |

## 116 user_guide

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 2 | b1 | button |  | 264,312 160x64 |
| 3 | b2 | button | 进料 | 440,312 160x64 |
| 4 | b3 | button | 退料 | 616,312 160x64 |
| 5 | b4 | button |  | 704,32 64x116 |
| 6 | b5 | button |  | 704,164 64x116 |
| 1 | b0 | button | 退出 | 24,312 160x64 |

## 117 slot_params

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 3 | b2 | button |  | 74,172 254x64 |
| 4 | b3 | button | 确定 | 482,304 160x64 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 1 | b0 | button |  | 74,24 254x64 |
| 2 | b1 | button |  | 74,96 254x64 |

## 118 vendor_set

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 4 | b3 | button |  | 710,24 66x168 |
| 5 | b4 | button |  | 710,206 66x168 |
| 6 | b5 | button |  | 348,24 348x62 |
| 7 | b6 | button |  | 348,96 348x62 |
| 3 | b2 | button |  | 74,172 254x64 |
| 1 | b0 | button |  | 74,24 254x64 |
| 2 | b1 | button |  | 74,96 254x64 |

## 119 filament_set

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 4 | b3 | button |  | 710,24 66x168 |
| 5 | b4 | button |  | 710,206 66x168 |
| 6 | b5 | button |  | 348,24 348x62 |
| 7 | b6 | button |  | 348,96 348x62 |
| 8 | b7 | button |  | 348,168 348x62 |
| 9 | b8 | button |  | 348,240 348x62 |
| 10 | b9 | button |  | 348,312 348x62 |
| 3 | b2 | button |  | 74,172 254x64 |
| 1 | b0 | button |  | 74,24 254x64 |
| 2 | b1 | button |  | 74,96 254x64 |

## 120 color_set

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 8 | b7 | button |  | 712,28 60x77 |
| 4 | color0 | button |  | 352,28 60x77 |
| 5 | color1 | button |  | 424,28 60x77 |
| 6 | color2 | button |  | 496,28 60x77 |
| 7 | color3 | button |  | 568,28 60x77 |
| 8 | color4 | button |  | 640,28 60x77 |
| 9 | color5 | button |  | 712,28 60x77 |
| 10 | color6 | button |  | 352,117 60x77 |
| 11 | color7 | button |  | 424,117 60x77 |
| 12 | color8 | button |  | 496,117 60x77 |
| 13 | color9 | button |  | 568,117 60x77 |
| 14 | color10 | button |  | 640,117 60x77 |
| 15 | color11 | button |  | 712,117 60x77 |
| 16 | color12 | button |  | 352,206 60x77 |
| 17 | color13 | button |  | 424,206 60x77 |
| 18 | color14 | button |  | 496,206 60x77 |
| 19 | color15 | button |  | 568,206 60x77 |
| 20 | color16 | button |  | 640,206 60x77 |
| 21 | color17 | button |  | 712,206 60x77 |
| 27 | color23 | button |  | 712,295 60x77 |
| 26 | color22 | button |  | 640,295 60x77 |
| 25 | color21 | button |  | 568,295 60x77 |
| 24 | color20 | button |  | 496,295 60x77 |
| 22 | color18 | button |  | 352,295 60x77 |
| 23 | color19 | button |  | 424,295 60x77 |
| 3 | b2 | button |  | 74,172 254x64 |
| 1 | b0 | button |  | 75,23 254x64 |
| 2 | b1 | button |  | 75,95 254x64 |

## 121 mc_print_set

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | 返回 | 432,384 160x64 |
| 2 | b1 | button | 打印 | 608,384 160x64 |
| 3 | b2 | button |  | 508,76 65x64 |
| 4 | b3 | button |  | 573,76 65x64 |
| 5 | b4 | button |  | 638,76 65x64 |
| 6 | b5 | button |  | 703,76 65x64 |
| 7 | b6 | button | ABS | 508,156 126x92 |
| 8 | b7 | button | PLA | 642,156 126x92 |
| 9 | b8 | button | PETG | 508,256 126x92 |
| 10 | b9 | button | LVGL | 642,256 126x92 |
| 12 | b11 | button |  | 142,30 108x77 |
| 11 | b10 | button |  | 30,30 108x77 |
| 13 | b12 | button |  | 254,30 108x77 |
| 14 | b13 | button |  | 366,30 108x77 |
| 15 | b14 | button |  | 30,111 108x77 |
| 16 | b15 | button |  | 142,111 108x77 |
| 17 | b16 | button |  | 254,111 108x77 |
| 18 | b17 | button |  | 366,111 108x77 |
| 19 | b18 | button |  | 30,192 108x77 |
| 20 | b19 | button |  | 142,192 108x77 |
| 21 | b20 | button |  | 254,192 108x77 |
| 22 | b21 | button |  | 366,192 108x77 |
| 23 | b22 | button |  | 30,273 108x77 |
| 24 | b23 | button |  | 142,273 108x77 |
| 25 | b24 | button |  | 254,273 108x77 |
| 26 | b25 | button |  | 366,273 108x77 |

## 122 unconnect_pop

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | 确定 | 490,312 140x60 |

## 123 vendor_pop

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | 确定 | 490,312 140x60 |

## 124 box_error_pop

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | 确定 | 490,312 140x60 |

## 125 data_pop

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | 确定 | 490,312 140x60 |

## 126 no_fila_pop

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | 确定 | 490,312 140x60 |

## 127 load_step1

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | 停止 | 24,312 160x64 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 2 | b1 | button | 下一步 | 616,312 160x64 |

## 128 load_step2

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | 重试 | 24,312 160x64 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 2 | b1 | button | 完成 | 616,312 160x64 |

## 132 load_error_pop

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 1 | b0 | button | Retry | 168,310 224x64 |
| 2 | b1 | button | Cancle | 408,310 224x64 |

## 133 box_setting

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 1 | b0 | button |  | 21,312 116x64 |
| 2 | b1 | button |  | 143,311 116x66 |
| 3 | b2 | button | 指南 | 264,310 163x66 |
| 4 | b3 | button |  | 326,35 66x38 |
| 5 | b4 | button |  | 698,37 65x36 |
| 6 | b5 | button |  | 325,145 66x37 |

## 134 fila_not_match

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button | 确定 | 490,312 140x60 |

## 135 box_drying

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 0 | b0 | button |  | 25,14 100x64 |
| 1 | b1 | button |  | 130,14 100x64 |
| 2 | b2 | button |  | 230,14 100x64 |
| 3 | b3 | button |  | 338,14 100x64 |
| 5 | b5 | button | 开始 | 598,307 174x64 |
| 33 | b33 | button |  | 16,400 140x80 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 6 | b6 | button |  | 412,167 358x59 |
| 7 | b7 | button |  | 413,235 176x65 |
| 8 | b8 | button |  | 595,237 177x59 |
| 4 | b4 | button | 退出 | 415,307 170x64 |
| 30 | t24 | text |  | 0,0 800x480 |
| 9 | b9 | button |  | 474,71 239x62 |
| 10 | b10 | button |  | 472,135 243x62 |
| 11 | b11 | button |  | 471,199 242x62 |
| 12 | b12 | button |  | 470,263 242x62 |
| 13 | b13 | button |  | 472,327 235x62 |
| 15 | b15 | button |  | 720,68 66x201 |
| 16 | b16 | button |  | 720,273 66x202 |
| 14 | b14 | button |  | 475,394 235x62 |
| 17 | b17 | button |  | 472,6 66x62 |
| 18 | b18 | button |  | 188,112 139x82 |
| 19 | b19 | button |  | 331,110 139x82 |
| 20 | b20 | button |  | 474,113 139x82 |
| 21 | b21 | button |  | 188,198 139x82 |
| 22 | b22 | button |  | 329,200 139x82 |
| 23 | b23 | button |  | 474,198 139x82 |
| 24 | b24 | button |  | 189,287 139x82 |
| 25 | b25 | button |  | 331,287 139x82 |
| 26 | b26 | button |  | 472,285 139x82 |
| 27 | b27 | button |  | 186,374 137x82 |
| 28 | b28 | button |  | 329,373 139x82 |
| 29 | b29 | button |  | 472,374 139x82 |
| 30 | b30 | button | 停止 | 415,305 356x70 |

## 136 drying_insp

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 33 | b33 | button |  | 16,400 140x80 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 1 | b1 | button | 开始 | 627,326 160x61 |
| 0 | b0 | button | 卸料 | 466,325 154x61 |
| 2 | b2 | button |  | 10,7 56x49 |

## 137 page0

| Reports | Widget | Type | Label | x,y wxh |
| --- | --- | --- | --- | --- |
| 19 | b21 | button |  | 705,89 63x55 |
| 18 | b19 | button |  | 640,89 63x55 |
| 17 | b22 | button |  | 705,32 63x55 |
| 16 | b18 | button |  | 640,32 63x55 |
| 1 | b0 | button |  | 24,312 115x64 |
| 2 | b1 | button | 卸载 | 264,312 160x64 |
| 3 | b2 | button | 进料 | 440,312 160x64 |
| 4 | b3 | button | 退料 | 616,312 160x64 |
| 5 | b4 | button |  | 24,208 104x56 |
| 34 | b34 | button |  | 172,400 140x80 |
| 35 | b35 | button |  | 328,400 144x80 |
| 36 | b36 | button |  | 488,400 140x80 |
| 37 | b37 | button |  | 644,400 140x80 |
| 33 | b33 | button |  | 16,400 140x80 |
| 6 | b5 | button |  | 208,208 104x56 |
| 7 | b6 | button |  | 314,208 104x56 |
| 8 | b7 | button |  | 420,208 104x56 |
| 9 | b8 | button |  | 526,208 104x56 |
| 10 | b9 | button |  | 24,24 104x184 |
| 11 | b10 | button |  | 208,24 104x184 |
| 12 | b11 | button |  | 314,24 104x184 |
| 13 | b12 | button |  | 420,24 104x184 |
| 14 | b13 | button |  | 526,24 104x184 |
| 71 | b14 | button |  | 229,26 65x55 |
| 72 | b15 | button |  | 334,26 65x55 |
| 73 | b16 | button |  | 441,26 65x55 |
| 74 | b17 | button |  | 547,26 65x55 |
| 20 | b23 | button |  | 139,310 115x64 |
| 21 | b20 | button |  | 642,188 128x72 |
| 42 | b41 | button |  | 216,120 80x64 |
| 47 | b46 | button |  | 216,192 80x64 |
| 48 | b47 | button |  | 304,192 80x64 |
| 43 | b42 | button |  | 304,120 80x64 |
| 44 | b43 | button |  | 392,120 80x64 |
| 49 | b48 | button |  | 392,192 80x64 |
| 50 | b49 | button |  | 480,192 80x64 |
| 45 | b44 | button |  | 480,120 80x64 |
| 46 | b45 | button |  | 568,120 80x64 |
| 51 | b50 | button |  | 568,192 80x64 |
| 40 | b39 | button |  | 660,32 108x72 |
| 41 | b40 | button |  | 660,120 108x136 |
| 24 | b24 | button |  | 611,265 170x44 |
