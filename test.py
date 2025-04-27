import json
import os
import sys

# 固定配置文件路径
CONFIG_DIR = "./Config"

# 只检查这个目标字段
TARGET_FIELD = "aio_config.ck_0.self_id"
FAKE_DATA_FIELD = "chip_simulate_fake_data"  # 新增字段检查

def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 无法加载 JSON 文件: {file_path}，错误: {e}")
        sys.exit(1)

def find_target_value(d, target_path):
    """递归查找目标路径对应的值"""
    parts = target_path.split('.')
    current = d
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current

def user_confirm(prompt, auto_mode=False):
    if auto_mode:
        return True
    else:
        while True:
            choice = input(f"{prompt} (y/n): ").lower()
            if choice in ['y', 'n']:
                return choice == 'y'
            else:
                print("⚠️ 请输入 'y' 或 'n'。")

def get_value_by_path(config, path):
    keys = path.split('.')
    current = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current

def main(auto_mode=False):
    # Step 1: 读取 config.json
    config_path = os.path.join(CONFIG_DIR, 'config.json')
    config = load_json(config_path)

    # 检查 chip_simulate_fake_data 是否存在
    fake_data_value = find_target_value(config, FAKE_DATA_FIELD)
    full_fake_data_path = FAKE_DATA_FIELD
    
    if fake_data_value is None:
        print(f"❌ 配置缺失: {full_fake_data_path}")
        sys.exit(1)
    elif not isinstance(fake_data_value, bool):  # 确保该字段是布尔类型
        print(f"❌ 配置错误: {full_fake_data_path} 应该是布尔值 (True/False)。")
        sys.exit(1)

    if fake_data_value:
        fake_data_output = f"{full_fake_data_path}: {fake_data_value}, 返回假数据的模拟计算"
    else:
        fake_data_output = f"{full_fake_data_path}: {fake_data_value}, 使用QVM的模拟计算"
    if not auto_mode:
        print(fake_data_output)
    
    # 用户确认 fake_data_value
    if not user_confirm(f"该配置是否正确？", auto_mode):
        print("❌ 配置错误，退出。")
        sys.exit(1)

    # 收集所有输出，方便自动模式最后一起确认
    collected_outputs = [fake_data_output]

    if 'chip' not in config:
        print("❌ config.json 中缺少 'chip' 字段！")
        sys.exit(1)

    chip_dict = config['chip']
    chip_list = list(chip_dict.keys())

    if not auto_mode:
        print(f"🔍 在 config.json 中找到以下 chip 类型: {chip_list}\n")

    # Step 2: 遍历每一个 chip
    for chip_name in chip_list:
        if not auto_mode:
            print(f"\n================== 检查 chip: {chip_name} ==================")
        chip_config = chip_dict[chip_name]

        # 只找目标字段
        value = find_target_value(chip_config, TARGET_FIELD)
        full_path = f"chip.{chip_name}.{TARGET_FIELD}"

        if value is None:
            print(f"❌ 配置缺失: {full_path}")
            sys.exit(1)
        
        output = f"{full_path}: {value}"
        if not auto_mode:
            print(output)
        collected_outputs.append(output)

        if not user_confirm("该配置是否正确？", auto_mode):
            print("❌ 配置错误，退出。")
            sys.exit(1)
        
        # Step 3: 检查对应的 ChipArchConfig_XXX.json 文件
        if chip_name == "72":
            arch_config_filename = "ChipArchConfig_D72.json"
        else:
            arch_config_filename = f"ChipArchConfig_{chip_name}.json"
        arch_config_path = os.path.join(CONFIG_DIR, arch_config_filename)

        if not os.path.exists(arch_config_path):
            print(f"❌ 找不到芯片架构配置文件: {arch_config_filename}")
            sys.exit(1)

        arch_config = load_json(arch_config_path)

        # 获取 QuantumChipArch.calc_method
        calc_method = get_value_by_path(arch_config, 'QuantumChipArch.calc_method')

        if calc_method is None:
            print(f"❌ {arch_config_filename} 中缺少 QuantumChipArch.calc_method 字段")
            sys.exit(1)
        
        if calc_method == 1:
            arch_output = f"{arch_config_filename} -> QuantumChipArch.calc_method: {calc_method}, 当前为模拟计算"
        else:
            arch_output = f"{arch_config_filename} -> QuantumChipArch.calc_method: {calc_method}, 当前为真实计算"
        if not auto_mode:
            print(arch_output)
        collected_outputs.append(arch_output)

        if not user_confirm("该配置是否正确？", auto_mode):
            print("❌ 配置错误，退出。")
            sys.exit(1)
    if not auto_mode:
        print("\n✅ 全部检查通过！")
    # 自动模式下，最后统一提示
    if auto_mode:
        print("\n=== 总览输出 ===")
        for item in collected_outputs:
            print(item)
        print("\n⚡ 请检查以上所有配置是否正确。")

    

if __name__ == '__main__':
    auto_mode = False

    if len(sys.argv) >= 2 and sys.argv[1] == '-a':
        auto_mode = True

    if not os.path.isdir(CONFIG_DIR):
        print(f"❌ 配置目录不存在: {CONFIG_DIR}")
        sys.exit(1)

    main(auto_mode)
