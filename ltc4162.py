import curses
from curses import wrapper
from smbus2 import SMBus
from time import sleep


# Create a new I2C bus
i2cbus = SMBus(1)

# Define I2C address of LTC4262
i2c_address = 0x68

# Battery shunt resistor (ohm)
RSNSB = 0.01 

# Number of LiFePO4 cells
# this needs to be hardcoded because the detected value becomes unavailable
# when the system is running on battery only
nr_of_cells = 4

#-------------------------------------
#Nothing to configure beyond this line
#-------------------------------------

device_version_enums = {
    0: "LTC4162_LAD",
    1: "LTC4162_L42",
    2: "LTC4162_L41",
    3: "LTC4162_L40",
    4: "LTC4162_FAD",
    5: "LTC4162_FFS",
    6: "LTC4162_FST",
    8: "LTC4162_SST",
    9: "LTC4162_SAD"
}


charger_state_enums = {
    4096: "bat_detect_failed_fault",
    2048: "battery_detection",
    512:  "absorb_charge",
    256:  "charger_suspended",
    64:   "cc_cv_charge",
    32:   "ntc_pause",
    16:   "timer_term",
    8:    "c_over_x_term",
    4:    "max_charge_time_fault",
    2:    "bat_missing_fault",
    1:    "bat_short_fault"
}


charger_status_enums = {
    32: "ilim_reg_active",
    16: "thermal_reg_active",
    8:  "vin_uvcl_active",
    4:  "iin_limit_active",
    2:  "constant_current",
    1:  "constant_voltage",
    0:  "charger_off"
}





def main(stdscr):
    #curses.start_color() #this is automagically initialized by wrapper
    curses.curs_set(0)

    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLUE)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLUE)

    green = curses.color_pair(1) | curses.A_BOLD
    red   = curses.color_pair(2) | curses.A_BOLD
    cyan  = curses.color_pair(3) | curses.A_BOLD
    csr   = curses.color_pair(4) | curses.A_BOLD
    labs  = curses.color_pair(5) | curses.A_BOLD

    stdscr.clear()

    while True:
    
        x = i2cbus.read_word_data(i2c_address, 0x43)
        detected_nr_of_cells = x & 15
        chem = (x >> 8) & 15

        detected_device = device_version_enums[chem]
        console_caption = "LTC4162 debug console"
        
        stdscr.addstr(0,0, "CSR", csr)
        stdscr.addstr(0,3, "Labs", labs)
        stdscr.addstr(0,8, console_caption, cyan)
        
        stdscr.addstr(0, 30, "| detected device:")
        stdscr.addstr(0, 49, detected_device, cyan)
        
        stdscr.addstr(0, 61, "| battery cells:")
        stdscr.addstr(0, 78, str(detected_nr_of_cells), cyan)
        
        stdscr.addstr(1, 0, "────────────────────────────────────────────────────────────────────────────────")
        
        x = i2cbus.read_word_data(i2c_address, 0x34)
        charger_state = charger_state_enums[x & 8191]
        stdscr.addstr(2, 0, "charger_state:")
        stdscr.addstr(2, 15, charger_state, cyan)

        x = i2cbus.read_word_data(i2c_address, 0x35)
        charger_status = charger_status_enums[x & 63]
        stdscr.addstr(2, 40, "charger_status:")
        stdscr.addstr(2, 56, charger_status, cyan)
        
        x = i2cbus.read_word_data(i2c_address, 0x1A)
        y = ((x & 31) + 1) * 0.001 / RSNSB
        stdscr.addstr(3, 0, "charge_current_setting:     A")
        stdscr.addstr(3, 24, str(y), cyan)
        
        x = i2cbus.read_word_data(i2c_address, 0x1B)
        y = nr_of_cells * (x * 0.0125 + 3.4125)
        stdscr.addstr(3, 40, "vcharge_setting:       V")
        stdscr.addstr(3, 57, str(y), cyan)
        
        x = i2cbus.read_word_data(i2c_address, 0x3F)
        y = round(x * 0.0215 - 264.4, 2)
        stdscr.addstr(4, 0, "die temperature:       °C")
        stdscr.addstr(4, 16, f"{y:>6.2f}", cyan)
        
        x = i2cbus.read_word_data(i2c_address, 0x2E)
        y = round(x / 18191 * 3.5 * nr_of_cells, 3)
        stdscr.addstr(4, 40, "v_recharge_lifepo4:        V")
        stdscr.addstr(4, 60, f"{y:>6.3f}", cyan)
        
        x = i2cbus.read_word_data(i2c_address, 0x29)
        en_c_over_x_term = x >> 2 & 1
        en_jeita = x & 1
        stdscr.addstr(6, 40, "CHARGER_CONFIG_BITS_REG: ")
        stdscr.addstr(6, 65, str(x), cyan)
        stdscr.addstr(7, 40, "en_c_over_x_term   : ")
        stdscr.addstr(7, 61, str(en_c_over_x_term), cyan)
        stdscr.addstr(8, 40, "en_jeita           :")
        stdscr.addstr(8, 61, str(en_jeita), cyan)
        
        
        x = i2cbus.read_word_data(i2c_address, 0x14)
        suspend_charger = x >> 5 & 1
        run_bsr = x >> 4 & 1
        telemetry_speed = x >> 3 & 1
        if telemetry_speed:
            tel_speed_text = "tel_high_speed"
        else:
            tel_speed_text = "tel_low_speed"
        force_telemetry_on = x >> 2 & 1
        mppt_en = x >> 1 & 1
        stdscr.addstr(10, 40, "CONFIG_BITS_REG    :")
        stdscr.addstr(10, 61, str(x), cyan)
        stdscr.addstr(11, 40, "suspend_charger    : ")
        stdscr.addstr(11, 61, str(suspend_charger), cyan)
        stdscr.addstr(12, 40, "run_bsr            : ")
        stdscr.addstr(12, 61, str(run_bsr), cyan)
        stdscr.addstr(13, 40, "telemetry_speed    : ")
        stdscr.addstr(13, 61, tel_speed_text, cyan)
        stdscr.addstr(14, 40, "force_telemetry_on : ")
        stdscr.addstr(14, 61, str(force_telemetry_on), cyan)
        stdscr.addstr(15, 40, "mppt_en            : ")
        stdscr.addstr(15, 61, str(mppt_en), cyan)
        
        
        x = i2cbus.read_word_data(i2c_address, 0x39)
        en_chg = x >> 8 & 1
        cell_count_err = x >> 7 & 1
        no_rt = x >> 5 & 1
        thermal_shutdown = x >> 4 & 1
        vin_ovlo = x >> 3 & 1
        vin_gt_vbat = x >> 2 & 1
        vin_gt_4p2v = x >> 1 & 1
        intvcc_gt_2p8v = x & 1
        
        
        stdscr.addstr(17, 40, "SYSTEM_STATUS_REG  :")
        stdscr.addstr(17, 61, str(x), cyan)
        stdscr.addstr(18, 40, "en_chg             : ")
        stdscr.addstr(18, 61, str(en_chg), cyan)
        stdscr.addstr(19, 40, "cell_count_err     : ")
        stdscr.addstr(19, 61, str(cell_count_err), cyan)
        stdscr.addstr(20, 40, "no_rt              : ")
        stdscr.addstr(20, 61, str(no_rt), cyan)
        stdscr.addstr(21, 40, "thermal_shutdown   : ")
        stdscr.addstr(21, 61, str(thermal_shutdown), cyan)
        stdscr.addstr(22, 40, "vin_ovlo           : ")
        stdscr.addstr(22, 61, str(vin_ovlo), cyan)
        stdscr.addstr(23, 40, "vin_gt_vbat        : ")
        stdscr.addstr(23, 61, str(vin_gt_vbat), cyan)
        stdscr.addstr(24, 40, "vin_gt_4p2v        : ")
        stdscr.addstr(24, 61, str(vin_gt_4p2v), cyan)
        stdscr.addstr(25, 40, "intvcc_gt_2p8v     : ")
        stdscr.addstr(25, 61, str(intvcc_gt_2p8v), cyan)
        
        
        x = i2cbus.read_word_data(i2c_address, 0x3B)
        in_v = round(x * 1.649 / 1000, 3)
        stdscr.addstr(5, 0, "input voltage  :        V")
        stdscr.addstr(5, 17, str(in_v), cyan)
        
        x = i2cbus.read_word_data(i2c_address, 0x3E)
        in_c = round(x * 1.466 / 10000, 3)
        stdscr.addstr(6, 0, "input current  :        A")
        stdscr.addstr(6, 17, f"{in_c:>6.3f}", cyan)
        
        x = i2cbus.read_word_data(i2c_address, 0x3C)
        y = round(x * 1.653 / 1000, 3)
        stdscr.addstr(7, 0, "output voltage :        V")
        stdscr.addstr(7, 17, f"{y:>6.3f}", cyan)
        
        x = i2cbus.read_word_data(i2c_address, 0x3A)
        batt_v = round(x * nr_of_cells * 0.1924 / 1000, 3)
        stdscr.addstr(8, 0, "battery voltage:        V")
        stdscr.addstr(8, 17, f"{batt_v:>6.3f}", cyan)

        x = i2cbus.read_word_data(i2c_address, 0x3D)
        if x >= 0x8000:
            y = x - 0x10000
        else:
            y = x
        batt_c = round(y * 1.466 / 10000, 3)
        stdscr.addstr(9, 0, "battery current:        A")
        stdscr.addstr(9, 17, f"{batt_c:>6.3f}", cyan)
        
        # Calculation of battery charger efficiency (no load)
        
        in_power = in_v * in_c
        stdscr.addstr(11, 0, "input power    :        W")
        stdscr.addstr(11, 17, f"{in_power:>6.3f}", cyan)

        stdscr.addstr(12, 0, "battery power  :        W")
        if batt_v > 0 and batt_c > 0:
            batt_power = batt_v * batt_c
            stdscr.addstr(12, 17, f"{batt_power:>6.3f}", cyan)
        else:
            batt_power = 0
            stdscr.addstr(12, 20, "N/A", cyan)
        
        stdscr.addstr(13, 0, "efficiency     :        %")
        stdscr.addstr(14, 0, "heat power     :        W")
        if batt_power > 0:
            efficiency = round(batt_power / in_power * 100, 2)
            heat_power = round(in_power - batt_power, 2)
            stdscr.addstr(13, 17, f"{efficiency:>5.2f}", cyan)
            stdscr.addstr(14, 17, f"{heat_power:>5.2f}", cyan)
            
        else:
            stdscr.addstr(13, 20, "N/A", cyan)
            stdscr.addstr(14, 20, "N/A", cyan)
        
        
        
        stdscr.refresh()
        
        sleep(.25)



wrapper(main)
